"""
Staging models for historical external datasets (Milestone C.1b).

These records are NEVER recommendation-eligible until a human promotes them
into the live catalog after checking a current official brand source.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, computed_field, field_validator


class StagedFoundationShade(BaseModel):
    """
    One historically imported shade row (e.g. The Pudding foundation-names).

    Approximate swatch hex/HSL are uncalibrated image extractions — not measurements.
    """

    id: str = Field(..., min_length=1, max_length=120)
    source_dataset: Literal["the_pudding_foundation_names"] = "the_pudding_foundation_names"
    source_file: str = Field(..., min_length=1)
    dataset_collection_note: str = Field(
        ...,
        description="Human-readable temporal applicability from the upstream dataset README.",
    )
    imported_at: datetime

    # Original CSV row preserved for audit (keys as in allShades.csv).
    raw: Dict[str, Any] = Field(default_factory=dict)

    # Normalized identity (stripped; null when upstream was empty/NA — never invented).
    brand: str = Field(..., min_length=1, max_length=120)
    product: str = Field(..., min_length=1, max_length=200)
    shade_name: Optional[str] = Field(default=None, max_length=120)
    shade_code: Optional[str] = Field(default=None, max_length=80)
    brand_shade_description: Optional[str] = Field(default=None, max_length=800)
    historical_retailer_url: Optional[str] = Field(default=None, max_length=800)

    # Approximate colors from historical swatch images — not calibrated.
    approx_hex: Optional[str] = Field(
        default=None,
        description="Normalized #RRGGBB from swatch extraction, or null if malformed.",
    )
    approx_hue: Optional[float] = None
    approx_sat: Optional[float] = None
    approx_lightness: Optional[float] = None
    approx_colorspace: Optional[str] = None

    # Always null on import — we do not invent depth/undertone from hex or prose.
    brand_reported_depth: None = None
    brand_reported_undertone: None = None

    verification_status: Literal["estimated"] = "estimated"
    metadata_verification_status: Literal["unreviewed"] = "unreviewed"
    matching_accuracy_status: Literal["not_evaluated"] = "not_evaluated"

    provenance_notes: str = Field(..., min_length=1, max_length=1200)
    uncertainty_notes: str = Field(..., min_length=1, max_length=1200)
    incomplete_flags: List[str] = Field(default_factory=list)

    @field_validator("brand", "product")
    @classmethod
    def strip_required(cls, value: str) -> str:
        return value.strip()

    @field_validator(
        "shade_name",
        "shade_code",
        "brand_shade_description",
        "historical_retailer_url",
        "approx_hex",
        "approx_colorspace",
        mode="before",
    )
    @classmethod
    def empty_to_none(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        if isinstance(value, str):
            return value.strip()
        return value

    @computed_field  # type: ignore[prop-decorator]
    @property
    def recommendation_eligible(self) -> bool:
        """Historical imports are never eligible for matcher recommendations."""
        return False

    def duplicate_key(self) -> tuple:
        """Stable key for detecting duplicate imports within one run."""
        return (
            self.brand.casefold(),
            self.product.casefold(),
            (self.shade_code or "").casefold(),
            (self.shade_name or "").casefold(),
            (self.approx_hex or "").casefold(),
            (self.brand_shade_description or "").casefold(),
        )


class ImportSkipRecord(BaseModel):
    row_number: int
    reason: str
    raw: Dict[str, Any] = Field(default_factory=dict)


class ImportReport(BaseModel):
    """Counts and notes from one import run."""

    source_path: str
    output_path: Optional[str] = None
    imported: int = 0
    skipped: int = 0
    duplicates: int = 0
    incomplete: int = 0
    skip_reasons: Dict[str, int] = Field(default_factory=dict)
    incomplete_flag_counts: Dict[str, int] = Field(default_factory=dict)
    brands_imported: int = 0
    products_imported: int = 0
    imported_at: datetime
    notes: List[str] = Field(default_factory=list)


class StagingManifest(BaseModel):
    """Wrapper written to the staging JSON file."""

    version: int = 1
    source_dataset: Literal["the_pudding_foundation_names"] = "the_pudding_foundation_names"
    attribution: str
    license_note: str
    color_caveat: str
    dataset_collection_note: str
    imported_at: datetime
    report: ImportReport
    shades: List[StagedFoundationShade]
    skipped: List[ImportSkipRecord] = Field(default_factory=list)
