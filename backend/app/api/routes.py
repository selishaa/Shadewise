"""HTTP endpoints for ShadeWise."""

from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse

from app.config import Settings, get_settings
from app.data.catalog_repository import CatalogDataError, list_shades, load_catalog
from app.data.staging_repository import (
    DISCLAIMER,
    StagingDataError,
    build_suggest,
    find_staged_shade,
    get_staging_manifest,
    list_products_for_brand,
    paginate,
    search_staged_shades,
    sort_staged_shades,
    staged_to_discovery_item,
)
from app.models.catalog import CatalogListResponse
from app.models.discovery import (
    DiscoveryBrandCount,
    DiscoveryBrandsResponse,
    DiscoveryProductCount,
    DiscoveryProductsResponse,
    DiscoverySearchResponse,
    DiscoveryShadeItem,
    DiscoverySuggestBrand,
    DiscoverySuggestProduct,
    DiscoverySuggestResponse,
    DiscoverySuggestShade,
)
from app.models.matching import MatchShadeRequest, MatchShadeResponse
from app.models.schemas import AnalyzeShadeRequest, AnalyzeShadeResponse
from app.services.analyze_rate_limit import analyze_rate_limiter
from app.services.shade_analyzer import ShadeAnalysisError, analyze_shade
from app.services.shade_matcher import match_shades


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "unknown"

router = APIRouter()

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


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
    http_request: Request,
    settings: Settings = Depends(get_settings),
) -> AnalyzeShadeResponse:
    """
    Interpret a foundation shade mismatch report via the LLM.

    Request body is validated by Pydantic before any AI call.
    Soft IP hourly + daily caps apply before OpenAI is contacted.
    """
    decision = analyze_rate_limiter.check_and_record(
        client_ip=_client_ip(http_request),
        per_ip_hour=settings.openai_rate_limit_per_ip_hour,
        daily_cap=settings.openai_daily_request_cap,
        count_toward_daily=settings.has_openai_key,
    )
    if not decision.allowed:
        raise HTTPException(status_code=decision.status_code, detail=decision.detail)

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


@router.get("/api/discover/shades", response_model=DiscoverySearchResponse)
async def discover_shades_endpoint(
    q: Optional[str] = Query(
        default=None,
        max_length=120,
        description="Free-text substring across brand, product, shade name/code, description.",
    ),
    brand: Optional[str] = Query(default=None, max_length=120),
    product: Optional[str] = Query(default=None, max_length=200),
    shade: Optional[str] = Query(
        default=None,
        max_length=120,
        description="Substring match on shade name, code, or description.",
    ),
    sort: Literal["brand", "product", "shade_name", "shade_code", "id"] = Query(
        default="brand"
    ),
    order: Literal["asc", "desc"] = Query(default="asc"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
) -> DiscoverySearchResponse:
    """
    Search historical (staged) foundation shades — discovery only.

    Separate from the verified /api/catalog. All items have recommendation_eligible=false.
    Does not call OpenAI. Default page_size is 20 (max 100).
    """
    try:
        manifest = get_staging_manifest()
    except StagingDataError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    filtered = search_staged_shades(
        manifest.shades, q=q, brand=brand, product=product, shade=shade
    )
    sorted_rows = sort_staged_shades(filtered, sort=sort, order=order)
    page_rows, total, total_pages = paginate(
        sorted_rows, page=page, page_size=page_size
    )

    return DiscoverySearchResponse(
        dataset="the_pudding_foundation_names",
        disclaimer=DISCLAIMER,
        color_caveat=manifest.color_caveat,
        page=page,
        page_size=page_size,
        total_matches=total,
        total_pages=total_pages,
        sort=sort,
        order=order,
        items=[staged_to_discovery_item(row) for row in page_rows],
    )


@router.get("/api/discover/shades/{staged_id}", response_model=DiscoveryShadeItem)
async def discover_shade_detail_endpoint(staged_id: str) -> DiscoveryShadeItem:
    """Fetch one historical staged shade by id (still unverified / not recommendable)."""
    try:
        get_staging_manifest()
    except StagingDataError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    shade = find_staged_shade(staged_id)
    if shade is None:
        raise HTTPException(status_code=404, detail=f"Staged shade not found: {staged_id}")
    return staged_to_discovery_item(shade)


@router.get("/api/discover/brands", response_model=DiscoveryBrandsResponse)
async def discover_brands_endpoint(
    q: Optional[str] = Query(
        default=None,
        max_length=120,
        description="Optional substring filter on brand name.",
    ),
    limit: int = Query(default=50, ge=1, le=200),
) -> DiscoveryBrandsResponse:
    """List brand names present in the historical staging dataset (with shade counts)."""
    try:
        manifest = get_staging_manifest()
    except StagingDataError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    counts: dict[str, int] = {}
    for shade in manifest.shades:
        counts[shade.brand] = counts.get(shade.brand, 0) + 1

    items = [
        DiscoveryBrandCount(brand=brand, shade_count=count)
        for brand, count in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0].casefold()))
    ]
    if q:
        needle = q.strip().casefold()
        items = [i for i in items if needle in i.brand.casefold()]

    return DiscoveryBrandsResponse(
        dataset="the_pudding_foundation_names",
        disclaimer=DISCLAIMER,
        total_brands=len(items),
        items=items[:limit],
    )


@router.get("/api/discover/products", response_model=DiscoveryProductsResponse)
async def discover_products_endpoint(
    brand: str = Query(..., min_length=1, max_length=120),
) -> DiscoveryProductsResponse:
    """List products for one brand (exact brand match, case-insensitive)."""
    try:
        get_staging_manifest()
    except StagingDataError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    rows = list_products_for_brand(brand)
    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"No historical products found for brand {brand!r}.",
        )
    items = [
        DiscoveryProductCount(brand=b, product=p, shade_count=c) for b, p, c in rows
    ]
    return DiscoveryProductsResponse(
        dataset="the_pudding_foundation_names",
        disclaimer=DISCLAIMER,
        brand=items[0].brand,
        total_products=len(items),
        items=items,
    )


@router.get("/api/discover/suggest", response_model=DiscoverySuggestResponse)
async def discover_suggest_endpoint(
    q: str = Query(..., min_length=1, max_length=120),
    limit: int = Query(default=8, ge=1, le=20),
) -> DiscoverySuggestResponse:
    """
    Compact autocomplete suggestions: matching brands, products, and shades.

    Prefer prefix matches. Never returns thousands of rows.
    """
    try:
        get_staging_manifest()
    except StagingDataError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    payload = build_suggest(q, limit=limit)
    return DiscoverySuggestResponse(
        dataset="the_pudding_foundation_names",
        disclaimer=DISCLAIMER,
        query=q.strip(),
        brands=[DiscoverySuggestBrand(**row) for row in payload["brands"]],
        products=[DiscoverySuggestProduct(**row) for row in payload["products"]],
        shades=[DiscoverySuggestShade(**row) for row in payload["shades"]],
    )


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
            "discover_shades": "/api/discover/shades",
            "discover_brands": "/api/discover/brands",
        }
    )
