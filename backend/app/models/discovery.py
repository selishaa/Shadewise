"""API models for historical foundation discovery (Milestone C.2)."""

from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field

ApproxSwatchWarning = (
    "Uncalibrated historical swatch-image extraction — NOT a calibrated color measurement. "
    "Do not treat as official brand color or matching proof."
)

HistoricalDataLabel = Literal["historical_unverified"]


class ApproxSwatchInfo(BaseModel):
    """Optional historical swatch color — always accompanied by a warning."""

    hex: Optional[str] = None
    hue: Optional[float] = None
    sat: Optional[float] = None
    lightness: Optional[float] = None
    colorspace: Optional[str] = None
    warning: str = ApproxSwatchWarning


class DiscoveryShadeItem(BaseModel):
    """One historical staged shade for discovery search results."""

    id: str
    brand: str
    product: str
    shade_name: Optional[str] = None
    shade_code: Optional[str] = None
    brand_shade_description: Optional[str] = None
    historical_retailer_url: Optional[str] = None
    approx_swatch: Optional[ApproxSwatchInfo] = None
    verification_status: str
    metadata_verification_status: str
    matching_accuracy_status: str
    recommendation_eligible: bool = False
    data_label: HistoricalDataLabel = "historical_unverified"
    availability_note: str = (
        "Historical retailer listing — availability may be outdated. "
        "Confirm on the current official brand page before relying on this shade."
    )
    incomplete_flags: List[str] = Field(default_factory=list)
    dataset_collection_note: str
    source_dataset: str = "the_pudding_foundation_names"


class DiscoverySearchResponse(BaseModel):
    dataset: str = "the_pudding_foundation_names"
    disclaimer: str
    color_caveat: str
    page: int
    page_size: int
    total_matches: int
    total_pages: int
    sort: str
    order: str
    items: List[DiscoveryShadeItem]


class DiscoveryBrandCount(BaseModel):
    brand: str
    shade_count: int


class DiscoveryBrandsResponse(BaseModel):
    dataset: str = "the_pudding_foundation_names"
    disclaimer: str
    total_brands: int
    items: List[DiscoveryBrandCount]


class DiscoveryProductCount(BaseModel):
    brand: str
    product: str
    shade_count: int


class DiscoveryProductsResponse(BaseModel):
    dataset: str = "the_pudding_foundation_names"
    disclaimer: str
    brand: str
    total_products: int
    items: List[DiscoveryProductCount]


class DiscoverySuggestBrand(BaseModel):
    brand: str
    shade_count: int
    match_type: Literal["prefix", "contains"] = "contains"


class DiscoverySuggestProduct(BaseModel):
    brand: str
    product: str
    shade_count: int
    match_type: Literal["prefix", "contains"] = "contains"


class DiscoverySuggestShade(BaseModel):
    id: str
    brand: str
    product: str
    shade_name: Optional[str] = None
    shade_code: Optional[str] = None
    match_type: Literal["prefix", "contains"] = "contains"


class DiscoverySuggestResponse(BaseModel):
    """Compact autocomplete payload — never dumps thousands of rows."""

    dataset: str = "the_pudding_foundation_names"
    disclaimer: str
    query: str
    brands: List[DiscoverySuggestBrand] = Field(default_factory=list)
    products: List[DiscoverySuggestProduct] = Field(default_factory=list)
    shades: List[DiscoverySuggestShade] = Field(default_factory=list)


SortField = Literal["brand", "product", "shade_name", "shade_code", "id"]
SortOrder = Literal["asc", "desc"]
