"""Shared pytest fixtures."""

import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.main import app


@pytest.fixture
def test_settings() -> Settings:
    return Settings(
        openai_api_key="",
        openai_model="gpt-4o-mini",
        cors_origins="http://localhost:3000",
    )


@pytest.fixture
def client(test_settings: Settings):
    app.dependency_overrides[get_settings] = lambda: test_settings
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_request_payload() -> dict:
    return {
        "brand": "Demo Cosmetics",
        "product": "Everyday Soft Matte Foundation",
        "shade_name": "Light 2 Warm",
        "depth_feedback": "correct",
        "undertone_issues": ["too_orange"],
        "description": "Depth looks right on my jaw but it turns orange by midday.",
        "wear_change": "yes",
    }
