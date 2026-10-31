"""
Catalog repository — JSON-backed for Milestone B.

Later (PostgreSQL): keep the same function names and swap the loader.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from app.models.catalog import CatalogProduct, FoundationShade

_CATALOG_PATH = Path(__file__).resolve().parent / "foundation_catalog.json"


class CatalogDataError(ValueError):
    """Raised when the catalog file is invalid or contains duplicates."""


def _load_raw_shades(path: Path = _CATALOG_PATH) -> List[dict]:
    if not path.exists():
        raise CatalogDataError(f"Catalog file not found: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CatalogDataError(f"Catalog JSON is invalid: {exc}") from exc

    shades = payload.get("shades")
    if not isinstance(shades, list):
        raise CatalogDataError("Catalog JSON must contain a 'shades' array.")
    return shades


def _validate_and_dedupe(raw_rows: List[dict]) -> List[FoundationShade]:
    items: List[FoundationShade] = []
    seen_ids = set()
    seen_keys = set()

    for index, row in enumerate(raw_rows):
        try:
            shade = FoundationShade.model_validate(row)
        except Exception as exc:  # noqa: BLE001 — surface row index for beginners
            raise CatalogDataError(
                f"Invalid catalog row at index {index} (id={row.get('id')!r}): {exc}"
            ) from exc

        if shade.id in seen_ids:
            raise CatalogDataError(f"Duplicate catalog id: {shade.id}")
        key = shade.duplicate_key()
        if key in seen_keys:
            raise CatalogDataError(
                "Duplicate shade identity "
                f"(brand={shade.brand!r}, product={shade.product!r}, "
                f"shade_name={shade.shade_name!r})"
            )
        seen_ids.add(shade.id)
        seen_keys.add(key)
        items.append(shade)

    return items


@lru_cache(maxsize=1)
def load_catalog() -> tuple:
    """Load and validate the full catalog once (cached). Returns a tuple for hashability."""
    return tuple(_validate_and_dedupe(_load_raw_shades()))


def reload_catalog() -> List[FoundationShade]:
    """Clear cache and reload — useful in tests."""
    load_catalog.cache_clear()
    return list(load_catalog())


def list_shades(
    *,
    brand: Optional[str] = None,
    product: Optional[str] = None,
    shade: Optional[str] = None,
    recommendation_eligible_only: bool = False,
) -> List[FoundationShade]:
    """
    Return catalog rows, optionally filtered.

    Filters are case-insensitive exact matches on brand / product / shade_name.
    """
    rows = list(load_catalog())

    if brand:
        needle = brand.strip().casefold()
        rows = [r for r in rows if r.brand.casefold() == needle]
    if product:
        needle = product.strip().casefold()
        rows = [r for r in rows if r.product.casefold() == needle]
    if shade:
        needle = shade.strip().casefold()
        rows = [r for r in rows if r.shade_name.casefold() == needle]
    if recommendation_eligible_only:
        rows = [r for r in rows if r.recommendation_eligible]

    return rows


def recommendation_eligible_shades() -> List[FoundationShade]:
    """Rows that Milestone C may use as match candidates (metadata-trusted)."""
    return [r for r in load_catalog() if r.recommendation_eligible]


def get_illustrative_catalog_products() -> List[CatalogProduct]:
    """
    Phase-1 analyze-shade UI hints.

    Only illustrative rows with both brand-reported depth and undertone filled.
    """
    products: List[CatalogProduct] = []
    for row in load_catalog():
        if row.verification_status != "illustrative":
            continue
        if row.brand_reported_depth is None or row.brand_reported_undertone is None:
            continue
        products.append(
            CatalogProduct(
                id=row.id,
                brand=row.brand,
                product=row.product,
                shade_name=row.shade_name,
                depth_family=row.brand_reported_depth,
                undertone_family=row.brand_reported_undertone,
                notes=row.notes
                or row.uncertainty_notes
                or "Illustrative catalog example.",
                data_status="illustrative",
            )
        )
    return products


def load_collection_template() -> dict:
    """Load the beginner data-collection template (not the live catalog)."""
    path = Path(__file__).resolve().parent / "catalog_entry_template.json"
    if not path.exists():
        raise CatalogDataError(f"Template file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def catalog_path() -> Path:
    return _CATALOG_PATH


def find_duplicate(
    candidate: FoundationShade,
    existing: Optional[List[FoundationShade]] = None,
) -> Optional[FoundationShade]:
    """Return an existing row that collides on id or duplicate_key, else None."""
    rows = existing if existing is not None else list(load_catalog())
    for row in rows:
        if row.id == candidate.id or row.duplicate_key() == candidate.duplicate_key():
            return row
    return None


def append_shade_to_catalog(
    shade: FoundationShade,
    *,
    path: Optional[Path] = None,
) -> FoundationShade:
    """
    Append one validated shade to the catalog JSON file and refresh the cache.

    Raises CatalogDataError on duplicate id/identity or validation failure.
    """
    target = Path(path) if path is not None else _CATALOG_PATH
    raw_rows = _load_raw_shades(target)
    existing = _validate_and_dedupe(raw_rows)

    collision = find_duplicate(shade, existing)
    if collision is not None:
        raise CatalogDataError(
            "Duplicate catalog entry blocked: "
            f"new id={shade.id!r} conflicts with existing id={collision.id!r} "
            f"(brand={collision.brand!r}, product={collision.product!r}, "
            f"shade_name={collision.shade_name!r})."
        )

    payload = json.loads(target.read_text(encoding="utf-8"))
    if not isinstance(payload.get("shades"), list):
        raise CatalogDataError("Catalog JSON must contain a 'shades' array.")

    row = shade.model_dump(mode="json", exclude={"recommendation_eligible"})
    payload["shades"].append(row)
    target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    load_catalog.cache_clear()
    return shade

