"""Structured AI response validation and mocked LLM tests."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import ValidationError

from app.config import Settings, get_settings
from app.main import app
from app.models.schemas import AnalyzeShadeRequest, ShadeAnalysis
from app.services.shade_analyzer import analyze_shade


def _valid_analysis(**overrides) -> dict:
    base = {
        "summary": "You reported correct depth with an orange cast that worsens after wear.",
        "reported_depth_match": "matches",
        "reported_color_issues": ["too orange"],
        "reported_wear_change": "yes",
        "possible_explanations": [
            "The formula may lean warmer/golden than your undertone.",
            "Oxidation after wear can increase orange appearance.",
        ],
        "undertone_adjustments_to_try": [
            "Investigate cooler or neutral options at a similar depth.",
        ],
        "suggested_next_steps": [
            "Swatch a cooler neighbor on the jawline in daylight.",
            "Recheck after 15 minutes of wear.",
        ],
        "uncertainties": [
            "Text alone cannot confirm your undertone or lighting conditions.",
        ],
        "analysis_vs_recommendation_note": (
            "This is interpretive analysis of what you reported, "
            "not a verified shade recommendation."
        ),
    }
    base.update(overrides)
    return base


def test_shade_analysis_accepts_valid_payload():
    analysis = ShadeAnalysis.model_validate(_valid_analysis())
    assert analysis.reported_depth_match == "matches"
    assert len(analysis.possible_explanations) >= 1


def test_shade_analysis_rejects_invalid_depth_label():
    with pytest.raises(ValidationError):
        ShadeAnalysis.model_validate(_valid_analysis(reported_depth_match="perfect"))


def test_shade_analysis_rejects_missing_note():
    payload = _valid_analysis()
    del payload["analysis_vs_recommendation_note"]
    with pytest.raises(ValidationError):
        ShadeAnalysis.model_validate(payload)


@pytest.mark.asyncio
async def test_analyze_shade_with_mocked_llm():
    """Mock OpenAI so tests never spend API credits."""
    settings = Settings(openai_api_key="sk-test-not-real", openai_model="gpt-4o-mini")
    request = AnalyzeShadeRequest(
        brand="Demo Cosmetics",
        product="Everyday Soft Matte Foundation",
        shade_name="Light 2 Warm",
        depth_feedback="correct",
        undertone_issues=["too_orange"],
        description="Looks good at first then turns orange.",
        wear_change="yes",
    )

    mock_parsed = ShadeAnalysis.model_validate(_valid_analysis())
    mock_message = MagicMock()
    mock_message.parsed = mock_parsed
    mock_message.refusal = None
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_completion = MagicMock()
    mock_completion.choices = [mock_choice]

    mock_client = AsyncMock()
    mock_client.beta.chat.completions.parse = AsyncMock(return_value=mock_completion)
    mock_client.close = AsyncMock()

    result = await analyze_shade(request, settings, client=mock_client)

    assert result.analysis.summary.startswith("You reported")
    assert result.prompt_version == "shade_analysis_v1"
    assert result.model_used == "gpt-4o-mini"
    assert len(result.guidance) >= 1
    assert all(item.data_status == "illustrative" for item in result.catalog_hints)
    mock_client.beta.chat.completions.parse.assert_awaited_once()


def test_analyze_endpoint_with_mocked_service(client, sample_request_payload):
    """HTTP layer test with the service mocked — still no live API."""
    from app.models.schemas import AnalyzeShadeResponse, GuidanceItem
    from app.prompts.shade_analysis import PROMPT_VERSION

    fake_response = AnalyzeShadeResponse(
        analysis=ShadeAnalysis.model_validate(_valid_analysis()),
        guidance=[
            GuidanceItem(
                title="Swatch in natural light",
                detail="Compare cooler and warmer options.",
                source="general_guidance",
            )
        ],
        catalog_hints=[],
        model_used="gpt-4o-mini",
        prompt_version=PROMPT_VERSION,
    )

    settings = Settings(openai_api_key="sk-test-not-real")
    app.dependency_overrides[get_settings] = lambda: settings

    with patch(
        "app.api.routes.analyze_shade",
        new=AsyncMock(return_value=fake_response),
    ):
        response = client.post("/api/analyze-shade", json=sample_request_payload)

    app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert "analysis" in body
    assert body["analysis"]["reported_wear_change"] == "yes"
    assert "guaranteed" not in body["analysis"]["analysis_vs_recommendation_note"].lower()
