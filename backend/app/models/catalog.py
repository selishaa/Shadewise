"""
Foundation catalog data model (Milestone B / B.1).

JSON-backed now; field names are ready for a future PostgreSQL table.

Two different ideas of "verified" (do not mix them up):
1) metadata_verification_status — did a human check brand/product/shade labels
   against a source page?
2) matching_accuracy_status — have we evidence this shade is a good *match*
   recommendation for someone? (Usually not until wear tests / gold-set eval.)
"""

from datetime import date
from typing import FrozenSet, List, Literal, Optional

from pydantic import BaseModel, Field, computed_field, field_validator


DepthFamily = Literal["fair", "light", "medium", "tan", "deep"]
UndertoneFamily = Literal["cool", "warm", "neutral", "olive"]

# Provenance of the *row contents* (where the text/labels came from).
VerificationStatus = Literal[
    "brand_verified",  # Copied from brand-published materials after human check
    "independently_measured",  # ShadeWise wear/measurement notes exist
    "estimated",  # Incomplete or uncertain — never recommend from this alone
    "illustrative",  # Fictional/demo teaching data — never recommend
]

# Did a human confirm identity + brand-published fields against a source?
MetadataVerificationStatus = Literal[
    "illustrative",  # Demo/teaching only
    "unreviewed",  # Draft row — not checked yet
    "source_checked",  # Human confirmed against source_url / packaging
]

# Separately: do we have evidence this shade is accurate for *matching*?
MatchingAccuracyStatus = Literal[
    "not_evaluated",  # Default for new real products
    "insufficient_evidence",  # Looked at, but not enough to claim match quality
    "wear_validated",  # Wear-tested / gold-set validated for matching use
]

RECOMMENDATION_ELIGIBLE_STATUSES: FrozenSet[str] = frozenset(
    {"brand_verified", "independently_measured"}
)


class FoundationShade(BaseModel):
    """
    One foundation shade row.

    Leave unknown fields null. Never invent brand wording or measurements.
    """

    id: str = Field(..., min_length=1, max_length=64)
    brand: str = Field(..., min_length=1, max_length=80)
    product: str = Field(..., min_length=1, max_length=120)
    shade_name: str = Field(
        ...,
        min_length=1,
        max_length=80,
        description="Marketing shade name as shown by the brand (required).",
    )
    shade_code: Optional[str] = Field(
        default=None,
        max_length=80,
        description="Brand shade code/SKU if different from the display name.",
    )
    brand_shade_description: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Exact brand-published shade blurb if available. Never invent.",
    )

    # --- Brand-reported classifications (from packaging / official page) ---
    brand_reported_depth: Optional[DepthFamily] = Field(
        default=None,
        description="Depth only if the brand states or clearly encodes it; else null.",
    )
    brand_reported_undertone: Optional[UndertoneFamily] = Field(
        default=None,
        description="Undertone only if the brand states it; else null.",
    )

    # --- Independently tested (leave null until real wear/lab work) ---
    independent_depth: Optional[DepthFamily] = Field(
        default=None,
        description="Depth from ShadeWise testing — separate from brand copy.",
    )
    independent_undertone: Optional[UndertoneFamily] = Field(
        default=None,
        description="Undertone from ShadeWise testing — separate from brand copy.",
    )
    independent_measurement_notes: Optional[str] = Field(
        default=None,
        max_length=800,
        description="How independent depth/undertone were observed (method, lighting, etc.).",
    )

    source_url: Optional[str] = Field(default=None, max_length=500)
    date_verified: Optional[date] = Field(
        default=None,
        description="Date metadata was last human-checked against the source.",
    )

    verification_status: VerificationStatus
    metadata_verification_status: MetadataVerificationStatus = Field(
        ...,
        description="Whether product/shade *metadata* was human-checked against a source.",
    )
    matching_accuracy_status: MatchingAccuracyStatus = Field(
        default="not_evaluated",
        description=(
            "Whether this shade has evidence for *recommendation accuracy*. "
            "Independent from metadata verification."
        ),
    )

    provenance_notes: str = Field(..., min_length=1, max_length=800)
    uncertainty_notes: Optional[str] = Field(default=None, max_length=800)
    notes: Optional[str] = Field(default=None, max_length=800)

    @field_validator("brand", "product", "shade_name", "provenance_notes")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        return value.strip()

    @field_validator(
        "shade_code",
        "brand_shade_description",
        "independent_measurement_notes",
        "source_url",
        "uncertainty_notes",
        "notes",
        mode="before",
    )
    @classmethod
    def empty_string_to_none(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        if isinstance(value, str):
            return value.strip()
        return value

    @computed_field  # type: ignore[prop-decorator]
    @property
    def recommendation_eligible(self) -> bool:
        """
        May be a *candidate* for a future matcher based on metadata trust.

        Does NOT mean matching accuracy is proven — check matching_accuracy_status.
        """
        return (
            self.verification_status in RECOMMENDATION_ELIGIBLE_STATUSES
            and self.metadata_verification_status == "source_checked"
            and self.matching_accuracy_status != "insufficient_evidence"
        )

    def duplicate_key(self) -> tuple:
        """Normalized identity for duplicate detection."""
        code = (self.shade_code or "").casefold()
        return (
            self.brand.casefold(),
            self.product.casefold(),
            self.shade_name.casefold(),
            code,
        )


class CatalogListResponse(BaseModel):
    """Response for GET /api/catalog."""

    items: List[FoundationShade]
    total: int
    recommendation_eligible_count: int


class CatalogProduct(BaseModel):
    """Illustrative catalog hint for analyze-shade UI — never a verified match."""

    id: str
    brand: str
    product: str
    shade_name: str
    depth_family: Literal["fair", "light", "medium", "tan", "deep"]
    undertone_family: Literal["cool", "warm", "neutral", "olive"]
    notes: str
    data_status: Literal["illustrative"] = "illustrative"
