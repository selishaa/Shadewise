"""Request/response models for the deterministic shade matcher (Milestone C)."""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


DepthFeedback = Literal["too_light", "too_dark", "correct", "unsure"]
# too_warm covers "too orange / too golden"; too_cool covers "too pink / too cool".
UndertoneIssue = Literal["too_warm", "too_cool", "none", "unsure"]


class MatchShadeRequest(BaseModel):
    """Inputs for local matching — no OpenAI call."""

    brand: Optional[str] = Field(default=None, max_length=80)
    product: Optional[str] = Field(default=None, max_length=120)
    shade_name: Optional[str] = Field(default=None, max_length=80)
    shade_code: Optional[str] = Field(default=None, max_length=80)
    depth_feedback: DepthFeedback = "unsure"
    undertone_issue: UndertoneIssue = "unsure"

    @field_validator("brand", "product", "shade_name", "shade_code", mode="before")
    @classmethod
    def empty_to_none(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        if isinstance(value, str):
            return value.strip()
        return value


class ShadeMatchCandidate(BaseModel):
    catalog_id: str
    brand: str
    product: str
    shade_name: str
    shade_code: Optional[str] = None
    selection_reasons: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    evidence_status: str = Field(
        ...,
        description=(
            "Honest evidence label. Catalog metadata verification is NOT proof of match accuracy."
        ),
    )


class MatchShadeResponse(BaseModel):
    matched_current_shade_id: Optional[str] = None
    recommendations: List[ShadeMatchCandidate] = Field(default_factory=list, max_length=3)
    no_match_reason: Optional[str] = None
    global_limitations: List[str] = Field(default_factory=list)
