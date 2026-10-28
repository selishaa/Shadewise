"""HTTP endpoints for ShadeWise Phase 1."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from app.config import Settings, get_settings
from app.models.schemas import AnalyzeShadeRequest, AnalyzeShadeResponse
from app.services.shade_analyzer import ShadeAnalysisError, analyze_shade

router = APIRouter()


@router.get("/health")
async def health(settings: Settings = Depends(get_settings)) -> dict:
    """Liveness check for local development and tests."""
    return {
        "status": "ok",
        "service": "shadewise-backend",
        "openai_configured": settings.has_openai_key,
    }


@router.post("/api/analyze-shade", response_model=AnalyzeShadeResponse)
async def analyze_shade_endpoint(
    request: AnalyzeShadeRequest,
    settings: Settings = Depends(get_settings),
) -> AnalyzeShadeResponse:
    """
    Interpret a foundation shade mismatch report via the LLM.

    Request body is validated by Pydantic before any AI call.
    """
    try:
        return await analyze_shade(request, settings)
    except ShadeAnalysisError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get("/")
async def root() -> JSONResponse:
    return JSONResponse(
        {
            "name": "ShadeWise API",
            "version": "0.1.0",
            "docs": "/docs",
            "health": "/health",
        }
    )
