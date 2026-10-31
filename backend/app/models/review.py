"""
Human review form for promoting a staged historical shade into the live catalog.

Nothing here invents depth/undertone/color. Reviewers copy only what they see
on a current official brand page (or leave fields null).
"""

from __future__ import annotations

from datetime import date
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator

from app.models.catalog import DepthFamily, UndertoneFamily


class ShadeReviewForm(BaseModel):
    """
    Filled by a human after checking the official brand page.

    Promotion requires explicit confirms — silent defaults are not enough.
    """

    staged_id: str = Field(..., min_length=1, max_length=120)

    official_source_url: str = Field(
        ...,
        min_length=8,
        max_length=500,
        description="Current official brand (or clearly official) product/shade URL.",
    )
    date_verified: date

    # Explicit human gates (must be true to promote).
    confirm_identity_matches_official_page: bool = False
    confirm_source_checked: bool = False
    availability_confirmed: bool = Field(
        default=False,
        description=(
            "True only if you confirmed the shade/product is still offered. "
            "Discontinued/unavailable shades must not be promoted as active recommendations."
        ),
    )

    # Identity as confirmed on the official page (required for live catalog).
    confirmed_brand: str = Field(..., min_length=1, max_length=80)
    confirmed_product: str = Field(..., min_length=1, max_length=120)
    confirmed_shade_name: str = Field(..., min_length=1, max_length=80)
    confirmed_shade_code: Optional[str] = Field(default=None, max_length=80)
    confirmed_brand_shade_description: Optional[str] = Field(default=None, max_length=500)

    # Optional enums — leave null unless the brand clearly states them. Never guess.
    brand_reported_depth: Optional[DepthFamily] = None
    brand_reported_undertone: Optional[UndertoneFamily] = None

    # Independent measurements stay null unless you document real evidence.
    independent_depth: Optional[DepthFamily] = None
    independent_undertone: Optional[UndertoneFamily] = None
    independent_measurement_notes: Optional[str] = Field(default=None, max_length=800)

    matching_accuracy_status: Literal["not_evaluated"] = "not_evaluated"

    catalog_id: Optional[str] = Field(
        default=None,
        max_length=64,
        description="Optional live catalog id slug; auto-generated if omitted.",
    )
    uncertainty_notes: Optional[str] = Field(default=None, max_length=800)
    notes: Optional[str] = Field(default=None, max_length=800)
    reviewer_notes: Optional[str] = Field(default=None, max_length=800)

    @field_validator(
        "confirmed_brand",
        "confirmed_product",
        "confirmed_shade_name",
        "official_source_url",
    )
    @classmethod
    def strip_required(cls, value: str) -> str:
        return value.strip()

    @field_validator(
        "confirmed_shade_code",
        "confirmed_brand_shade_description",
        "independent_measurement_notes",
        "uncertainty_notes",
        "notes",
        "reviewer_notes",
        "catalog_id",
        mode="before",
    )
    @classmethod
    def empty_to_none(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        if isinstance(value, str):
            return value.strip()
        return value


class PromotionRejection(BaseModel):
    reasons: List[str]


class PromotionResult(BaseModel):
    promoted: bool
    catalog_id: Optional[str] = None
    rejection_reasons: List[str] = Field(default_factory=list)
    message: str
