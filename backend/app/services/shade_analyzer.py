"""
Shade analysis orchestration.

Flow:
1. Build versioned prompts from validated request data.
2. Call OpenAI with structured outputs → ShadeAnalysis.
3. Attach deterministic guidance + illustrative catalog (never invent SKUs).
"""

from typing import Optional

from openai import APIConnectionError, APIStatusError, APITimeoutError, AsyncOpenAI, OpenAIError

from app.config import Settings
from app.data.catalog import get_catalog, get_general_guidance
from app.models.schemas import AnalyzeShadeRequest, AnalyzeShadeResponse, ShadeAnalysis
from app.prompts.shade_analysis import PROMPT_VERSION, SYSTEM_PROMPT, build_user_prompt


class ShadeAnalysisError(Exception):
    """Raised when analysis cannot complete for a user-visible reason."""

    def __init__(self, message: str, status_code: int = 503):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


async def analyze_shade(
    request: AnalyzeShadeRequest,
    settings: Settings,
    client: Optional[AsyncOpenAI] = None,
) -> AnalyzeShadeResponse:
    """Run LLM analysis and combine with deterministic guidance."""
    if not settings.has_openai_key:
        raise ShadeAnalysisError(
            "OpenAI API key is not configured. "
            "Copy backend/.env.example to backend/.env and set OPENAI_API_KEY.",
            status_code=503,
        )

    analysis = await _call_llm(request, settings, client)

    guidance = get_general_guidance(
        depth_feedback=request.depth_feedback,
        undertone_issues=list(request.undertone_issues),
    )

    # Illustrative catalog only — never presented as verified recommendations.
    catalog_hints = get_catalog()[:3]

    return AnalyzeShadeResponse(
        analysis=analysis,
        guidance=guidance,
        catalog_hints=catalog_hints,
        model_used=settings.openai_model,
        prompt_version=PROMPT_VERSION,
    )


async def _call_llm(
    request: AnalyzeShadeRequest,
    settings: Settings,
    client: Optional[AsyncOpenAI],
) -> ShadeAnalysis:
    owns_client = client is None
    if client is None:
        client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            timeout=settings.openai_timeout_seconds,
        )

    try:
        # Structured outputs: OpenAI returns JSON that must match ShadeAnalysis.
        completion = await client.beta.chat.completions.parse(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_user_prompt(request)},
            ],
            response_format=ShadeAnalysis,
            max_tokens=settings.openai_max_tokens,
            temperature=0.3,
        )
    except APITimeoutError as exc:
        raise ShadeAnalysisError(
            "The shade analysis timed out. Please try again in a moment.",
            status_code=504,
        ) from exc
    except APIConnectionError as exc:
        raise ShadeAnalysisError(
            "Could not reach the AI service. Check your network and try again.",
            status_code=503,
        ) from exc
    except APIStatusError as exc:
        raise ShadeAnalysisError(
            "The AI service returned an error. Please try again later.",
            status_code=502,
        ) from exc
    except OpenAIError as exc:
        raise ShadeAnalysisError(
            "Shade analysis failed due to an unexpected AI service error.",
            status_code=502,
        ) from exc
    finally:
        if owns_client:
            await client.close()

    parsed = completion.choices[0].message.parsed
    if parsed is None:
        refusal = completion.choices[0].message.refusal
        raise ShadeAnalysisError(
            refusal or "The AI did not return a usable structured analysis.",
            status_code=502,
        )

    return parsed
