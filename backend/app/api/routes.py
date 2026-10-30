"""HTTP endpoints for ShadeWise."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from app.config import Settings, get_settings
from app.data.catalog_repository import CatalogDataError, list_shades, load_catalog
from app.models.catalog import CatalogListResponse
from app.models.matching import MatchShadeRequest, MatchShadeResponse
from app.models.schemas import AnalyzeShadeRequest, AnalyzeShadeResponse
from app.services.shade_analyzer import ShadeAnalysisError, analyze_shade
from app.services.shade_matcher import match_shades

router = APIRouter()


@router.get("/health")
async def health(settings: Settings = Depends(get_settings)) -> dict:
    """Liveness check for local development and tests."""
    return {
        "status": "ok",
        "service": "shadewise-backend",
        "openai_configured": settings.has_openai_key,
    }


@router.get("/api/catalog", response_model=CatalogListResponse)
async def catalog_endpoint(
    brand: Optional[str] = Query(default=None, max_length=80),
    product: Optional[str] = Query(default=None, max_length=120),
    shade: Optional[str] = Query(
        default=None,
        max_length=80,
        description="Exact shade name/code (case-insensitive).",
    ),
    recommendation_eligible_only: bool = Query(
        default=False,
        description=(
            "If true, return only brand_verified / independently_measured rows "
            "(excludes illustrative, estimated, and other unverified demo data)."
        ),
    ),
) -> CatalogListResponse:
    """
    List foundation shades from the local demonstration catalog.

    Filters use case-insensitive exact match. This endpoint does not call OpenAI.
    """
    try:
        items = list_shades(
            brand=brand,
            product=product,
            shade=shade,
            recommendation_eligible_only=recommendation_eligible_only,
        )
    except CatalogDataError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    eligible_count = sum(1 for item in items if item.recommendation_eligible)
    return CatalogListResponse(
        items=items,
        total=len(items),
        recommendation_eligible_count=eligible_count,
    )


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


@router.post("/api/match-shades", response_model=MatchShadeResponse)
async def match_shades_endpoint(request: MatchShadeRequest) -> MatchShadeResponse:
    """
    Deterministic shade matching from verified catalog metadata.

    Does not call OpenAI. Safe to exercise via /docs during local development.
    Does not claim matching accuracy — only conservative label comparisons.
    """
    try:
        catalog = load_catalog()
    except CatalogDataError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return match_shades(request, catalog)


@router.get("/")
async def root() -> JSONResponse:
    return JSONResponse(
        {
            "name": "ShadeWise API",
            "version": "0.1.0",
            "docs": "/docs",
            "health": "/health",
            "catalog": "/api/catalog",
            "match_shades": "/api/match-shades",
        }
    )
