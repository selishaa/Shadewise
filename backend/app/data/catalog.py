"""
Catalog helpers used by shade analysis.

- get_general_guidance: deterministic tips from form answers (unchanged behavior).
- get_catalog: illustrative UI hints only (never recommendation-eligible rows).
"""

from typing import List

from app.data.catalog_repository import get_illustrative_catalog_products
from app.models.catalog import CatalogProduct
from app.models.schemas import GuidanceItem


def get_catalog() -> List[CatalogProduct]:
    """Illustrative demo rows for analyze-shade results panel."""
    return get_illustrative_catalog_products()


def get_general_guidance(depth_feedback: str, undertone_issues: List[str]) -> List[GuidanceItem]:
    """
    Deterministic guidance based on form selections.

    This is code, not the LLM — so it stays predictable and never invents SKUs.
    """
    items: List[GuidanceItem] = [
        GuidanceItem(
            title="Swatch in natural light",
            detail=(
                "Compare the current shade and one cooler / one warmer option "
                "along the jawline in daylight. Give each 10–15 minutes to settle."
            ),
            source="general_guidance",
        ),
        GuidanceItem(
            title="Separate depth from undertone",
            detail=(
                "If depth feels right but color looks off (orange, pink, ashy), "
                "prioritize undertone neighbors at the same depth before changing depth."
            ),
            source="general_guidance",
        ),
    ]

    if depth_feedback == "too_dark":
        items.append(
            GuidanceItem(
                title="Depth may be one step deep",
                detail=(
                    "When depth is wrong, try one shade lighter in the same undertone family "
                    "before jumping across brands or undertones."
                ),
                source="general_guidance",
            )
        )
    elif depth_feedback == "too_light":
        items.append(
            GuidanceItem(
                title="Depth may be one step light",
                detail=(
                    "Try one shade deeper in the same undertone family. "
                    "A shade that is too light often looks chalky or ashy as it oxidizes."
                ),
                source="general_guidance",
            )
        )

    if "too_orange" in undertone_issues:
        items.append(
            GuidanceItem(
                title="Orange cast → investigate cooler or less warm",
                detail=(
                    "An orange cast often means the formula runs warm/golden for your skin. "
                    "Look for cooler, neutral, or olive labels at a similar depth — "
                    "verify in person; labels vary by brand."
                ),
                source="general_guidance",
            )
        )
    if "too_pink" in undertone_issues:
        items.append(
            GuidanceItem(
                title="Pink cast → investigate warmer or more neutral",
                detail=(
                    "A pink or rosy cast often means the shade leans cool. "
                    "Try warmer or neutral options at the same depth, then reassess after wear."
                ),
                source="general_guidance",
            )
        )

    items.append(
        GuidanceItem(
            title="No verified product matches yet",
            detail=(
                "ShadeWise does not claim cross-brand shade equivalences until a "
                "verified catalog row is matched by the recommendation algorithm "
                "(Milestone C). Use AI analysis for interpretation and this guidance "
                "for what to test next."
            ),
            source="general_guidance",
        )
    )

    return items
