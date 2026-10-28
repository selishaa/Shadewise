"""Request/response schemas and AI structured-output models."""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


# --- Limits for safety and cost control ---
MAX_TEXT_LEN = 500
MAX_BRAND_LEN = 80
MAX_PRODUCT_LEN = 120
MAX_SHADE_LEN = 80


DepthFeedback = Literal["too_light", "correct", "too_dark", "unsure"]
UndertoneIssue = Literal[
    "too_orange",
    "too_pink",
    "too_yellow",
    "too_ashy",
    "too_red",
    "looks_gray",
    "unsure",
    "none",
]
WearChange = Literal["yes", "no", "unsure"]


class AnalyzeShadeRequest(BaseModel):
    """Validated user input from the Find Your Shade form."""

    brand: str = Field(..., min_length=1, max_length=MAX_BRAND_LEN)
    product: str = Field(..., min_length=1, max_length=MAX_PRODUCT_LEN)
    shade_name: str = Field(..., min_length=1, max_length=MAX_SHADE_LEN)
    depth_feedback: DepthFeedback
    undertone_issues: List[UndertoneIssue] = Field(default_factory=list, max_length=6)
    description: str = Field(default="", max_length=MAX_TEXT_LEN)
    wear_change: WearChange = "unsure"

    @field_validator("brand", "product", "shade_name", "description")
    @classmethod
    def strip_whitespace(cls, value: str) -> str:
        return value.strip()

    @field_validator("undertone_issues")
    @classmethod
    def dedupe_issues(cls, value: List[UndertoneIssue]) -> List[UndertoneIssue]:
        seen = set()
        unique: List[UndertoneIssue] = []
        for item in value:
            if item not in seen:
                seen.add(item)
                unique.append(item)
        return unique


class ShadeAnalysis(BaseModel):
    """
    Structured LLM output.

    Distinguishes reported facts from speculative explanations.
    The model must not invent shade equivalences or product claims.
    """

    summary: str = Field(
        ...,
        description="Plain-language summary of the user's reported mismatch.",
        max_length=600,
    )
    reported_depth_match: Literal["matches", "too_light", "too_dark", "unclear"] = Field(
        ...,
        description="What the user reported about shade depth, not a measured fact.",
    )
    reported_color_issues: List[str] = Field(
        default_factory=list,
        description="Color/undertone issues the user reported.",
        max_length=8,
    )
    reported_wear_change: Literal["yes", "no", "unsure"] = Field(
        ...,
        description="Whether the user said the shade changes after wear.",
    )
    possible_explanations: List[str] = Field(
        default_factory=list,
        description="Plausible explanations framed as hypotheses, not diagnoses.",
        max_length=6,
    )
    undertone_adjustments_to_try: List[str] = Field(
        default_factory=list,
        description="Directions to investigate (e.g. cooler, less orange), not product SKUs.",
        max_length=6,
    )
    suggested_next_steps: List[str] = Field(
        default_factory=list,
        description="Concrete swatch tests or questions the user can try next.",
        max_length=8,
    )
    uncertainties: List[str] = Field(
        default_factory=list,
        description="What the AI cannot know from text alone.",
        max_length=6,
    )
    analysis_vs_recommendation_note: str = Field(
        ...,
        description="Clear statement that this is interpretive analysis, not a verified match.",
        max_length=400,
    )


class GuidanceItem(BaseModel):
    """General guidance or illustrative catalog hint (not a verified match)."""

    title: str
    detail: str
    source: Literal["general_guidance", "illustrative_catalog"]


class CatalogProduct(BaseModel):
    """Tiny local demo catalog entry — explicitly illustrative unless verified."""

    id: str
    brand: str
    product: str
    shade_name: str
    depth_family: Literal["fair", "light", "medium", "tan", "deep"]
    undertone_family: Literal["cool", "warm", "neutral", "olive"]
    notes: str
    data_status: Literal["illustrative"] = "illustrative"


class AnalyzeShadeResponse(BaseModel):
    """API response combining AI analysis with grounded guidance only."""

    analysis: ShadeAnalysis
    guidance: List[GuidanceItem] = Field(default_factory=list)
    catalog_hints: List[CatalogProduct] = Field(
        default_factory=list,
        description="Illustrative catalog rows for learning UI only — not recommendations.",
    )
    model_used: Optional[str] = None
    prompt_version: str
