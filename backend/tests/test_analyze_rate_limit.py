"""Soft abuse controls for /api/analyze-shade."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.main import app
from app.models.schemas import AnalyzeShadeResponse, ShadeAnalysis
from app.services.analyze_rate_limit import analyze_rate_limiter


@pytest.fixture(autouse=True)
def _reset_limiter():
    analyze_rate_limiter.reset()
    yield
    analyze_rate_limiter.reset()


def _payload() -> dict:
    return {
        "brand": "Demo Cosmetics",
        "product": "Everyday Soft Matte Foundation",
        "shade_name": "Light 2 Warm",
        "shade_code": "L2W",
        "depth_feedback": "correct",
        "undertone_issues": ["too_orange"],
        "description": "Turns orange by midday.",
        "wear_change": "yes",
    }


def test_analyze_rate_limit_returns_429_after_ip_cap():
    settings = Settings(
        openai_api_key="",
        openai_model="gpt-4o-mini",
        openai_rate_limit_per_ip_hour=2,
        openai_daily_request_cap=100,
        cors_origins="http://localhost:3000",
    )
    app.dependency_overrides[get_settings] = lambda: settings
    try:
        with TestClient(app) as client:
            first = client.post("/api/analyze-shade", json=_payload())
            second = client.post("/api/analyze-shade", json=_payload())
            third = client.post("/api/analyze-shade", json=_payload())
        # No key → 503 after passing rate limit for first two.
        assert first.status_code == 503
        assert second.status_code == 503
        assert third.status_code == 429
        assert "too many" in third.json()["detail"].lower()
    finally:
        app.dependency_overrides.clear()


def test_analyze_daily_cap_returns_429_when_openai_configured():
    settings = Settings(
        openai_api_key="sk-test-not-real",
        openai_model="gpt-4o-mini",
        openai_rate_limit_per_ip_hour=50,
        openai_daily_request_cap=1,
        cors_origins="http://localhost:3000",
    )
    fake_analysis = ShadeAnalysis(
        summary="Depth looks right; warmth may be high.",
        reported_depth_match="matches",
        reported_color_issues=["too orange"],
        reported_wear_change="yes",
        possible_explanations=["Formula may run warm."],
        undertone_adjustments_to_try=["Try cooler at same depth."],
        suggested_next_steps=["Swatch in daylight."],
        uncertainties=["Lighting unknown."],
        analysis_vs_recommendation_note="Interpretive only — not a verified match.",
    )
    fake_response = AnalyzeShadeResponse(
        analysis=fake_analysis,
        guidance=[],
        catalog_hints=[],
        model_used="gpt-4o-mini",
        prompt_version="shade_analysis_v1",
    )

    app.dependency_overrides[get_settings] = lambda: settings
    try:
        with patch(
            "app.api.routes.analyze_shade",
            new_callable=AsyncMock,
            return_value=fake_response,
        ):
            with TestClient(app) as client:
                first = client.post("/api/analyze-shade", json=_payload())
                second = client.post("/api/analyze-shade", json=_payload())
        assert first.status_code == 200
        assert second.status_code == 429
        assert "capacity" in second.json()["detail"].lower()
    finally:
        app.dependency_overrides.clear()
