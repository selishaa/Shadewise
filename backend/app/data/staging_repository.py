"""
Read-only access to the historical staging dataset (Milestone C.2).

Uses the imported Pudding staging JSON — does not copy rows into the live catalog.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

from app.models.discovery import (
    ApproxSwatchInfo,
    ApproxSwatchWarning,
    DiscoveryShadeItem,
    SortField,
    SortOrder,
)
from app.models.staging import StagedFoundationShade, StagingManifest
from app.services.pudding_importer import load_staging_manifest

DEFAULT_STAGING_PATH = (
    Path(__file__).resolve().parent / "staging" / "pudding_all_shades.json"
)

_staging_path_override: Optional[Path] = None

DISCLAIMER = (
    "These records are historical and unverified. They are for discovery only, "
    "not shade recommendations. recommendation_eligible is always false here. "
    "Use the verified /api/catalog and /api/match-shades endpoints for matcher input."
)


class StagingDataError(ValueError):
    """Raised when staging data cannot be loaded."""


def set_staging_path_override(path: Optional[Path]) -> None:
    """Test helper — point discovery at a fixture staging file."""
    global _staging_path_override
    _staging_path_override = path
    load_staging_cached.cache_clear()


def get_staging_path() -> Path:
    if _staging_path_override is not None:
        return Path(_staging_path_override)
    return DEFAULT_STAGING_PATH


@lru_cache(maxsize=4)
def load_staging_cached(path_str: str) -> StagingManifest:
    path = Path(path_str)
    if not path.exists():
        raise StagingDataError(
            f"Staging file not found: {path}. "
            "Import with: python -m scripts.import_pudding_shades"
        )
    try:
        return load_staging_manifest(path)
    except Exception as exc:  # noqa: BLE001
        raise StagingDataError(f"Invalid staging file {path}: {exc}") from exc


def get_staging_manifest() -> StagingManifest:
    return load_staging_cached(str(get_staging_path().resolve()))


def staged_to_discovery_item(shade: StagedFoundationShade) -> DiscoveryShadeItem:
    approx = None
    if any(
        [
            shade.approx_hex,
            shade.approx_hue is not None,
            shade.approx_sat is not None,
            shade.approx_lightness is not None,
        ]
    ):
        approx = ApproxSwatchInfo(
            hex=shade.approx_hex,
            hue=shade.approx_hue,
            sat=shade.approx_sat,
            lightness=shade.approx_lightness,
            colorspace=shade.approx_colorspace,
            warning=ApproxSwatchWarning,
        )

    return DiscoveryShadeItem(
        id=shade.id,
        brand=shade.brand,
        product=shade.product,
        shade_name=shade.shade_name,
        shade_code=shade.shade_code,
        brand_shade_description=shade.brand_shade_description,
        historical_retailer_url=shade.historical_retailer_url,
        approx_swatch=approx,
        verification_status=shade.verification_status,
        metadata_verification_status=shade.metadata_verification_status,
        matching_accuracy_status=shade.matching_accuracy_status,
        recommendation_eligible=False,
        incomplete_flags=list(shade.incomplete_flags),
        dataset_collection_note=shade.dataset_collection_note,
        source_dataset=shade.source_dataset,
    )


def _matches_query(shade: StagedFoundationShade, needle: str) -> bool:
    haystacks = [
        shade.brand,
        shade.product,
        shade.shade_name or "",
        shade.shade_code or "",
        shade.brand_shade_description or "",
    ]
    return any(needle in (h.casefold()) for h in haystacks)


def match_rank(text: Optional[str], needle: str) -> int:
    """
    Lower is better: 0 = prefix, 1 = word-prefix / contains-as-word, 2 = substring, 999 = no match.
    """
    if not text:
        return 999
    hay = text.casefold().strip()
    n = needle.casefold().strip()
    if not n:
        return 999
    if hay.startswith(n):
        return 0
    # Word-boundary-ish: " fit me" style partial words
    padded = f" {hay.replace('/', ' ').replace('-', ' ')}"
    if f" {n}" in padded:
        return 1
    if n in hay:
        return 2
    return 999


def search_staged_shades(
    shades: Sequence[StagedFoundationShade],
    *,
    q: Optional[str] = None,
    brand: Optional[str] = None,
    product: Optional[str] = None,
    shade: Optional[str] = None,
) -> List[StagedFoundationShade]:
    """
    Filter staged shades.

    - brand / product: case-insensitive substring on that field
    - shade: substring on shade_name, shade_code, or description
    - q: substring across brand, product, name, code, description
    """
    rows = list(shades)

    if brand:
        needle = brand.strip().casefold()
        rows = [r for r in rows if needle in r.brand.casefold()]
    if product:
        needle = product.strip().casefold()
        rows = [r for r in rows if needle in r.product.casefold()]
    if shade:
        needle = shade.strip().casefold()
        rows = [
            r
            for r in rows
            if (r.shade_name and needle in r.shade_name.casefold())
            or (r.shade_code and needle in r.shade_code.casefold())
            or (r.brand_shade_description and needle in r.brand_shade_description.casefold())
        ]
    if q:
        needle = q.strip().casefold()
        rows = [r for r in rows if _matches_query(r, needle)]

    return rows


def _sort_key(shade: StagedFoundationShade, field: SortField) -> Tuple:
    empty_last = "\uffff"

    def text(value: Optional[str]) -> str:
        if value is None or not str(value).strip():
            return empty_last
        return value.casefold()

    if field == "brand":
        return (text(shade.brand), text(shade.product), text(shade.shade_name), shade.id)
    if field == "product":
        return (text(shade.product), text(shade.brand), text(shade.shade_name), shade.id)
    if field == "shade_name":
        return (text(shade.shade_name), text(shade.brand), shade.id)
    if field == "shade_code":
        return (text(shade.shade_code), text(shade.brand), shade.id)
    return (shade.id.casefold(),)


def sort_staged_shades(
    shades: Sequence[StagedFoundationShade],
    *,
    sort: SortField = "brand",
    order: SortOrder = "asc",
) -> List[StagedFoundationShade]:
    reverse = order == "desc"
    return sorted(shades, key=lambda s: _sort_key(s, sort), reverse=reverse)


def paginate(
    shades: Sequence[StagedFoundationShade],
    *,
    page: int,
    page_size: int,
) -> Tuple[List[StagedFoundationShade], int, int]:
    """Return (page_slice, total_matches, total_pages)."""
    total = len(shades)
    total_pages = max(1, (total + page_size - 1) // page_size) if total else 0
    if total == 0:
        return [], 0, 0
    page = max(1, page)
    start = (page - 1) * page_size
    end = start + page_size
    return list(shades[start:end]), total, total_pages


def find_staged_shade(shade_id: str) -> Optional[StagedFoundationShade]:
    for shade in get_staging_manifest().shades:
        if shade.id == shade_id:
            return shade
    return None


def list_products_for_brand(brand: str) -> List[Tuple[str, str, int]]:
    """Return [(brand, product, shade_count), ...] for an exact brand match (case-insensitive)."""
    needle = brand.strip().casefold()
    counts: dict[tuple[str, str], int] = {}
    display: dict[tuple[str, str], tuple[str, str]] = {}
    for shade in get_staging_manifest().shades:
        if shade.brand.casefold() != needle:
            continue
        key = (shade.brand.casefold(), shade.product.casefold())
        counts[key] = counts.get(key, 0) + 1
        display[key] = (shade.brand, shade.product)
    rows = [
        (display[key][0], display[key][1], counts[key])
        for key in counts
    ]
    rows.sort(key=lambda r: r[1].casefold())
    return rows


def build_suggest(query: str, *, limit: int = 8) -> dict:
    """
    Ranked autocomplete groups for brand / product / shade.
    Caps each group so the UI never receives thousands of rows.
    """
    needle = query.strip()
    if len(needle) < 1:
        return {"brands": [], "products": [], "shades": []}

    shades = get_staging_manifest().shades
    brand_counts: dict[str, int] = {}
    brand_display: dict[str, str] = {}
    product_counts: dict[tuple[str, str], int] = {}
    product_display: dict[tuple[str, str], tuple[str, str]] = {}
    shade_hits: List[Tuple[int, StagedFoundationShade]] = []

    for shade in shades:
        brand_counts[shade.brand.casefold()] = brand_counts.get(shade.brand.casefold(), 0) + 1
        brand_display[shade.brand.casefold()] = shade.brand
        pkey = (shade.brand.casefold(), shade.product.casefold())
        product_counts[pkey] = product_counts.get(pkey, 0) + 1
        product_display[pkey] = (shade.brand, shade.product)

        shade_score = min(
            match_rank(shade.shade_name, needle),
            match_rank(shade.shade_code, needle),
            match_rank(shade.brand_shade_description, needle),
            # Allow brand/product typed queries to surface example shades
            match_rank(f"{shade.brand} {shade.product}", needle) + 1,
        )
        if shade_score < 999:
            shade_hits.append((shade_score, shade))

    brand_hits = []
    for key, count in brand_counts.items():
        rank = match_rank(brand_display[key], needle)
        if rank < 999:
            brand_hits.append((rank, brand_display[key], count))
    brand_hits.sort(key=lambda row: (row[0], -row[2], row[1].casefold()))

    product_hits = []
    for key, count in product_counts.items():
        brand_name, product_name = product_display[key]
        rank = min(match_rank(product_name, needle), match_rank(f"{brand_name} {product_name}", needle))
        if rank < 999:
            product_hits.append((rank, brand_name, product_name, count))
    product_hits.sort(key=lambda row: (row[0], -row[3], row[1].casefold(), row[2].casefold()))

    shade_hits.sort(
        key=lambda row: (
            row[0],
            row[1].brand.casefold(),
            row[1].product.casefold(),
            (row[1].shade_name or row[1].shade_code or "").casefold(),
        )
    )

    # Deduplicate shade suggestions by identity, keep best rank
    seen_shade = set()
    shades_out = []
    for rank, shade in shade_hits:
        identity = (
            shade.brand.casefold(),
            shade.product.casefold(),
            (shade.shade_name or "").casefold(),
            (shade.shade_code or "").casefold(),
        )
        if identity in seen_shade:
            continue
        seen_shade.add(identity)
        shades_out.append(
            {
                "id": shade.id,
                "brand": shade.brand,
                "product": shade.product,
                "shade_name": shade.shade_name,
                "shade_code": shade.shade_code,
                "match_type": "prefix" if rank == 0 else "contains",
            }
        )
        if len(shades_out) >= limit:
            break

    return {
        "brands": [
            {
                "brand": name,
                "shade_count": count,
                "match_type": "prefix" if rank == 0 else "contains",
            }
            for rank, name, count in brand_hits[:limit]
        ],
        "products": [
            {
                "brand": brand_name,
                "product": product_name,
                "shade_count": count,
                "match_type": "prefix" if rank == 0 else "contains",
            }
            for rank, brand_name, product_name, count in product_hits[:limit]
        ],
        "shades": shades_out,
    }
