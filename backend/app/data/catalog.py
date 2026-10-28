"""
Tiny local demonstration catalog.

All entries are explicitly ILLUSTRATIVE. They exist so the UI can show how
catalog-backed hints would look — they are NOT verified product matches
and must never be presented as real shade recommendations.
"""

from typing import List

from app.models.schemas import CatalogProduct, GuidanceItem


_ILLUSTRATIVE_CATALOG: List[CatalogProduct] = [
    CatalogProduct(
        id="demo-1",
        brand="Demo Cosmetics",
        product="Everyday Soft Matte Foundation",
        shade_name="Light 2 Neutral",
        depth_family="light",
        undertone_family="neutral",
        notes="Illustrative only — shows a neutral light depth family label.",
    ),
    CatalogProduct(
        id="demo-2",
        brand="Demo Cosmetics",
        product="Everyday Soft Matte Foundation",
        shade_name="Light 2 Cool",
        depth_family="light",
        undertone_family="cool",
        notes="Illustrative only — cooler sibling of Light 2 Neutral.",
    ),
    CatalogProduct(
        id="demo-3",
        brand="Demo Cosmetics",
        product="Everyday Soft Matte Foundation",
        shade_name="Light 2 Warm",
        depth_family="light",
        undertone_family="warm",
        notes="Illustrative only — warmer sibling; useful for 'too pink' discussions.",
    ),
    CatalogProduct(
        id="demo-4",
        brand="Demo Cosmetics",
        product="Sheer Glow Tint",
        shade_name="Medium Olive 1",
        depth_family="medium",
        undertone_family="olive",
        notes="Illustrative only — olive family for greying/orange mismatch talks.",
    ),
]


def get_catalog() -> List[CatalogProduct]:
    return list(_ILLUSTRATIVE_CATALOG)


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
                "ShadeWise Phase 1 does not claim cross-brand shade equivalences. "
                "Use AI analysis for interpretation and this guidance for what to test next."
            ),
            source="general_guidance",
        )
    )

    return items
