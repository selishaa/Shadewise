"""
Offline importer for The Pudding foundation-names allShades.csv (Milestone C.1b).

Safety rules:
- Writes only to a staging file — never foundation_catalog.json.
- Does not invent shade names, depth, or undertone.
- Every row is estimated / unreviewed / not_evaluated / not recommendation-eligible.
- Approximate hex/HSL are historical swatch extractions, not calibrated color.
"""

from __future__ import annotations

import csv
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from app.models.staging import (
    ImportReport,
    ImportSkipRecord,
    StagedFoundationShade,
    StagingManifest,
)

# Temporal applicability from The Pudding foundation-names README (Mar 2021).
PUDDING_COLLECTION_NOTE = (
    "The Pudding foundation-names: Sephora scrape 2021-01-11; "
    "Ulta scrape 2021-01-18; allShades last modified 2021-03-17. "
    "Historical retailer listings — not a current brand catalog."
)

PUDDING_ATTRIBUTION = (
    "Shade data adapted from The Pudding's foundation-names dataset "
    "(https://github.com/the-pudding/data/tree/master/foundation-names), "
    "used in the essay The Naked Truth (https://pudding.cool/2021/03/foundation-names). "
    "Repository data/code is offered under the MIT License (see "
    "app/data/external/pudding/LICENSE). Brand names, product copy, and retailer "
    "swatch images remain third-party intellectual property; MIT covers The Pudding's "
    "compilation/scripts, not brand trademarks or CDN images."
)

PUDDING_LICENSE_NOTE = (
    "Upstream repository license: MIT (Copyright (c) 2019 The Pudding). "
    "Include the MIT copyright notice with substantial portions of the Software. "
    "Do not rehost Ulta/Sephora swatch images from imgSrc URLs."
)

COLOR_CAVEAT = (
    "approx_hex / approx_hue / approx_sat / approx_lightness come from historical "
    "swatch-image color extraction. They are uncalibrated and must not be treated "
    "as measured foundation color or matching proof."
)

REQUIRED_COLUMNS = (
    "brand",
    "product",
    "url",
    "description",
    "imgSrc",
    "imgAlt",
    "name",
    "specific",
    "colorspace",
    "hex",
    "hue",
    "sat",
    "lightness",
)

_HEX_RE = re.compile(r"^#?([0-9A-Fa-f]{6})$")
_NA_VALUES = frozenset({"", "na", "n/a", "none", "null"})


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _is_missing(value: Optional[str]) -> bool:
    if value is None:
        return True
    return value.strip().casefold() in _NA_VALUES


def _clean_text(value: Optional[str]) -> Optional[str]:
    if value is None or _is_missing(value):
        return None
    text = value.strip()
    # Retailer UI noise sometimes appended to descriptions.
    text = re.sub(r"\s+selected\s*$", "", text, flags=re.IGNORECASE).strip()
    return text or None


def _normalize_hex(value: Optional[str]) -> Optional[str]:
    if value is None or _is_missing(value):
        return None
    match = _HEX_RE.fullmatch(value.strip())
    if not match:
        return None
    return f"#{match.group(1).upper()}"


def _parse_float(value: Optional[str]) -> Optional[float]:
    if value is None or _is_missing(value):
        return None
    try:
        return float(value.strip())
    except ValueError:
        return None


def _slug_part(value: str, fallback: str = "unknown") -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
    return cleaned[:48] or fallback


def _make_id(
    brand: str,
    product: str,
    shade_name: Optional[str],
    shade_code: Optional[str],
    approx_hex: Optional[str],
    row_number: int,
) -> str:
    identity = shade_code or shade_name or (approx_hex or "").lstrip("#") or f"row-{row_number}"
    return (
        f"pudding-{_slug_part(brand)}-{_slug_part(product)}-"
        f"{_slug_part(identity, fallback=f'row-{row_number}')}-{row_number}"
    )[:120]


def _identity_present(shade_name: Optional[str], shade_code: Optional[str], description: Optional[str]) -> bool:
    return bool(shade_name or shade_code or description)


def row_to_staged(
    raw: Dict[str, str],
    *,
    row_number: int,
    source_file: str,
    imported_at: datetime,
) -> Tuple[Optional[StagedFoundationShade], Optional[str], List[str]]:
    """
    Convert one CSV row.

    Returns (shade, skip_reason, incomplete_flags).
    """
    brand = _clean_text(raw.get("brand"))
    product = _clean_text(raw.get("product"))
    if not brand or not product:
        return None, "missing_brand_or_product", []

    shade_name = _clean_text(raw.get("name"))
    shade_code = _clean_text(raw.get("specific"))
    description = _clean_text(raw.get("description")) or _clean_text(raw.get("imgAlt"))
    url = _clean_text(raw.get("url"))
    approx_hex = _normalize_hex(raw.get("hex"))
    approx_hue = _parse_float(raw.get("hue"))
    approx_sat = _parse_float(raw.get("sat"))
    approx_lightness = _parse_float(raw.get("lightness"))
    colorspace = _clean_text(raw.get("colorspace"))

    flags: List[str] = []
    if shade_name is None:
        flags.append("missing_shade_name")
    if shade_code is None:
        flags.append("missing_shade_code")
    if description is None:
        flags.append("missing_description")
    if url is None:
        flags.append("missing_url")
    if approx_hex is None:
        flags.append("malformed_or_missing_hex")
    if approx_hue is None or approx_sat is None or approx_lightness is None:
        flags.append("incomplete_hsl")
    if not _identity_present(shade_name, shade_code, description):
        return None, "no_shade_identity", flags

    uncertainty_parts = [
        "Imported from a historical retailer scrape; product lines and shade lists may be outdated.",
        "Depth and undertone were not inferred — left null.",
        COLOR_CAVEAT,
    ]
    if flags:
        uncertainty_parts.append("Incomplete flags: " + ", ".join(flags) + ".")

    shade = StagedFoundationShade(
        id=_make_id(brand, product, shade_name, shade_code, approx_hex, row_number),
        source_file=source_file,
        dataset_collection_note=PUDDING_COLLECTION_NOTE,
        imported_at=imported_at,
        raw=dict(raw),
        brand=brand,
        product=product,
        shade_name=shade_name,
        shade_code=shade_code,
        brand_shade_description=description,
        historical_retailer_url=url,
        approx_hex=approx_hex,
        approx_hue=approx_hue,
        approx_sat=approx_sat,
        approx_lightness=approx_lightness,
        approx_colorspace=colorspace,
        provenance_notes=(
            f"Imported offline from The Pudding foundation-names allShades.csv "
            f"(source file {source_file}, CSV row {row_number}). {PUDDING_ATTRIBUTION}"
        ),
        uncertainty_notes=" ".join(uncertainty_parts),
        incomplete_flags=flags,
    )
    return shade, None, flags


def import_all_shades_csv(
    input_path: Path,
    *,
    output_path: Optional[Path] = None,
    write_skipped: bool = True,
) -> StagingManifest:
    """
    Import allShades.csv into a StagingManifest.

    If output_path is set, write JSON there (never foundation_catalog.json).
    """
    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"CSV not found: {input_path}")

    imported_at = _utc_now()
    shades: List[StagedFoundationShade] = []
    skipped: List[ImportSkipRecord] = []
    seen_keys: set = set()
    skip_reasons: Counter[str] = Counter()
    incomplete_flag_counts: Counter[str] = Counter()

    with input_path.open(newline="", encoding="utf-8", errors="replace") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError("CSV has no header row.")
        missing_cols = [c for c in REQUIRED_COLUMNS if c not in reader.fieldnames]
        if missing_cols:
            raise ValueError(
                "CSV missing required columns: "
                + ", ".join(missing_cols)
                + f". Found: {list(reader.fieldnames)}"
            )

        for row_number, raw in enumerate(reader, start=2):  # header is line 1
            # Normalize keys / values to plain strings
            cleaned_raw = {
                key: ("" if value is None else str(value)) for key, value in raw.items()
            }
            shade, skip_reason, flags = row_to_staged(
                cleaned_raw,
                row_number=row_number,
                source_file=input_path.name,
                imported_at=imported_at,
            )
            if skip_reason:
                skip_reasons[skip_reason] += 1
                skipped.append(
                    ImportSkipRecord(
                        row_number=row_number,
                        reason=skip_reason,
                        raw=cleaned_raw if write_skipped else {},
                    )
                )
                continue

            assert shade is not None
            key = shade.duplicate_key()
            if key in seen_keys:
                skip_reasons["duplicate"] += 1
                skipped.append(
                    ImportSkipRecord(
                        row_number=row_number,
                        reason="duplicate",
                        raw=cleaned_raw if write_skipped else {},
                    )
                )
                continue
            seen_keys.add(key)

            for flag in flags:
                incomplete_flag_counts[flag] += 1
            shades.append(shade)

    duplicates = skip_reasons.get("duplicate", 0)
    skipped_total = sum(skip_reasons.values())
    incomplete = sum(1 for s in shades if s.incomplete_flags)
    brands = {s.brand.casefold() for s in shades}
    products = {(s.brand.casefold(), s.product.casefold()) for s in shades}

    report = ImportReport(
        source_path=str(input_path),
        output_path=str(output_path) if output_path else None,
        imported=len(shades),
        skipped=skipped_total,
        duplicates=duplicates,
        incomplete=incomplete,
        skip_reasons=dict(skip_reasons),
        incomplete_flag_counts=dict(incomplete_flag_counts),
        brands_imported=len(brands),
        products_imported=len(products),
        imported_at=imported_at,
        notes=[
            "Staging only — not merged into foundation_catalog.json.",
            "No records are recommendation_eligible.",
            "Do not treat approx_* color fields as calibrated measurements.",
        ],
    )

    manifest = StagingManifest(
        attribution=PUDDING_ATTRIBUTION,
        license_note=PUDDING_LICENSE_NOTE,
        color_caveat=COLOR_CAVEAT,
        dataset_collection_note=PUDDING_COLLECTION_NOTE,
        imported_at=imported_at,
        report=report,
        shades=shades,
        skipped=skipped if write_skipped else [],
    )

    if output_path is not None:
        output_path = Path(output_path)
        if output_path.resolve().name == "foundation_catalog.json":
            raise ValueError(
                "Refusing to write staging data to foundation_catalog.json. "
                "Use a path under app/data/staging/ instead."
            )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            manifest.model_dump_json(indent=2),
            encoding="utf-8",
        )
        report.output_path = str(output_path)

    return manifest


def load_staging_manifest(path: Path) -> StagingManifest:
    path = Path(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    return StagingManifest.model_validate(payload)


def filter_staged_shades(
    shades: Sequence[StagedFoundationShade],
    *,
    brand: Optional[str] = None,
    product: Optional[str] = None,
    shade: Optional[str] = None,
) -> List[StagedFoundationShade]:
    """Case-insensitive filters for CLI inspection."""
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
    return rows


def summarize_brands(shades: Iterable[StagedFoundationShade], limit: int = 30) -> List[Tuple[str, int]]:
    counts: Counter[str] = Counter(s.brand for s in shades)
    return counts.most_common(limit)
