"""
Promote a human-reviewed staged shade into the live foundation catalog.

Safety:
- Staging rows alone are never recommendation-eligible.
- Promotion requires explicit source_checked + identity + availability confirms.
- Does not invent depth, undertone, names, or color measurements.
- matching_accuracy_status stays not_evaluated unless review insists otherwise
  (review model locks it to not_evaluated).
- Refuses duplicates and preserves existing catalog rows (including NARS).
"""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import List, Optional, Sequence

from app.data.catalog_repository import (
    CatalogDataError,
    append_shade_to_catalog,
    find_duplicate,
    load_catalog,
)
from app.models.catalog import FoundationShade
from app.models.review import PromotionResult, ShadeReviewForm
from app.models.staging import StagedFoundationShade
from app.services.pudding_importer import load_staging_manifest

SWATCH_WARNING = (
    "WARNING: Historical approx_hex / HSL values are uncalibrated swatch-image "
    "extractions from a 2021 retailer scrape. They are NOT official brand colors "
    "and must NOT be copied into the live catalog as measurements."
)


class PromotionError(ValueError):
    """Raised when a promotion cannot proceed."""


def find_staged_by_id(
    shades: Sequence[StagedFoundationShade], staged_id: str
) -> Optional[StagedFoundationShade]:
    for shade in shades:
        if shade.id == staged_id:
            return shade
    return None


def find_staged_exact(
    shades: Sequence[StagedFoundationShade],
    *,
    brand: Optional[str] = None,
    product: Optional[str] = None,
    shade_name: Optional[str] = None,
    shade_code: Optional[str] = None,
) -> List[StagedFoundationShade]:
    """
    Exact case-insensitive match on provided fields.

    At least one of brand / product / shade_name / shade_code must be set.
    """
    if not any([brand, product, shade_name, shade_code]):
        raise ValueError("Provide at least one exact filter: brand, product, shade_name, shade_code.")

    rows = list(shades)
    if brand is not None:
        needle = brand.strip().casefold()
        rows = [r for r in rows if r.brand.casefold() == needle]
    if product is not None:
        needle = product.strip().casefold()
        rows = [r for r in rows if r.product.casefold() == needle]
    if shade_name is not None:
        needle = shade_name.strip().casefold()
        rows = [r for r in rows if (r.shade_name or "").casefold() == needle]
    if shade_code is not None:
        needle = shade_code.strip().casefold()
        rows = [r for r in rows if (r.shade_code or "").casefold() == needle]
    return rows


def format_staged_for_review(shade: StagedFoundationShade) -> str:
    """Human-readable card with explicit swatch warnings."""
    lines = [
        f"Staged ID:     {shade.id}",
        f"Brand:         {shade.brand}",
        f"Product:       {shade.product}",
        f"Shade name:    {shade.shade_name!r}",
        f"Shade code:    {shade.shade_code!r}",
        f"Description:   {shade.brand_shade_description!r}",
        f"Historical URL:{shade.historical_retailer_url}",
        f"Dataset note:  {shade.dataset_collection_note}",
        f"Imported at:   {shade.imported_at}",
        f"Status:        {shade.verification_status} / "
        f"{shade.metadata_verification_status} / "
        f"{shade.matching_accuracy_status}",
        f"Eligible?:     {shade.recommendation_eligible} (staging is never eligible)",
        "",
        "--- Approximate historical swatch (NOT a measurement) ---",
        SWATCH_WARNING,
        f"approx_hex:       {shade.approx_hex}",
        f"approx_hue:       {shade.approx_hue}",
        f"approx_sat:       {shade.approx_sat}",
        f"approx_lightness: {shade.approx_lightness}",
        f"approx_colorspace:{shade.approx_colorspace}",
        "",
        f"Incomplete flags: {', '.join(shade.incomplete_flags) or '(none)'}",
        f"Provenance: {shade.provenance_notes[:300]}...",
        f"Uncertainty: {shade.uncertainty_notes[:300]}...",
    ]
    return "\n".join(lines)


def build_review_template(shade: StagedFoundationShade) -> dict:
    """
    Blank-ish review JSON prefilled with historical identity hints.

    Depth/undertone stay null. Confirms default to false so promotion fails
    until the human sets them intentionally.
    """
    suggested_name = shade.shade_name or shade.shade_code or ""
    return {
        "staged_id": shade.id,
        "official_source_url": "REPLACE_WITH_CURRENT_OFFICIAL_BRAND_URL",
        "date_verified": date.today().isoformat(),
        "confirm_identity_matches_official_page": False,
        "confirm_source_checked": False,
        "availability_confirmed": False,
        "confirmed_brand": shade.brand,
        "confirmed_product": shade.product,
        "confirmed_shade_name": suggested_name,
        "confirmed_shade_code": shade.shade_code,
        "confirmed_brand_shade_description": None,
        "brand_reported_depth": None,
        "brand_reported_undertone": None,
        "independent_depth": None,
        "independent_undertone": None,
        "independent_measurement_notes": None,
        "matching_accuracy_status": "not_evaluated",
        "catalog_id": None,
        "uncertainty_notes": (
            "Promoted from historical staging after human check of the official page. "
            "Historical swatch hex was not treated as a color measurement."
        ),
        "notes": (
            f"Historical retailer URL was: {shade.historical_retailer_url}. "
            f"Staged id: {shade.id}."
        ),
        "reviewer_notes": (
            "Fill official_source_url. Set the three confirm_* / availability flags to true "
            "only after checking the live official page. Leave depth/undertone null if unsure."
        ),
        "_warnings": [
            SWATCH_WARNING,
            "Do not copy approx_hex into the live catalog.",
            "Do not invent depth or undertone.",
            "Discontinued products: leave availability_confirmed=false (promotion will be rejected).",
        ],
        "_historical_snapshot": {
            "brand": shade.brand,
            "product": shade.product,
            "shade_name": shade.shade_name,
            "shade_code": shade.shade_code,
            "brand_shade_description": shade.brand_shade_description,
            "historical_retailer_url": shade.historical_retailer_url,
            "approx_hex": shade.approx_hex,
            "dataset_collection_note": shade.dataset_collection_note,
            "provenance_notes": shade.provenance_notes,
            "raw": shade.raw,
        },
    }


def _slug(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
    return cleaned or "shade"


def suggest_catalog_id(review: ShadeReviewForm) -> str:
    if review.catalog_id:
        return review.catalog_id[:64]
    parts = [
        _slug(review.confirmed_brand)[:20],
        _slug(review.confirmed_product)[:24],
        _slug(review.confirmed_shade_code or review.confirmed_shade_name)[:16],
    ]
    return "-".join(p for p in parts if p)[:64]


def collect_rejection_reasons(
    review: ShadeReviewForm,
    staged: Optional[StagedFoundationShade],
    *,
    existing_catalog: Optional[Sequence[FoundationShade]] = None,
) -> List[str]:
    reasons: List[str] = []

    if staged is None:
        reasons.append(f"Staged id not found: {review.staged_id!r}")
        return reasons

    if not review.confirm_identity_matches_official_page:
        reasons.append(
            "confirm_identity_matches_official_page must be true "
            "(explicit human confirmation required)."
        )
    if not review.confirm_source_checked:
        reasons.append(
            "confirm_source_checked must be true before metadata can be source_checked."
        )
    if not review.availability_confirmed:
        reasons.append(
            "availability_confirmed must be true. Discontinued/unavailable shades "
            "are not promoted into the active recommendation catalog."
        )

    url = review.official_source_url.strip().casefold()
    if url.startswith("replace_") or "replace_with" in url:
        reasons.append("official_source_url still looks like a template placeholder.")
    if not (
        review.official_source_url.startswith("http://")
        or review.official_source_url.startswith("https://")
    ):
        reasons.append("official_source_url must be an http(s) URL.")

    if not review.confirmed_shade_name.strip():
        reasons.append("confirmed_shade_name is required for the live catalog.")

    if review.matching_accuracy_status != "not_evaluated":
        reasons.append("matching_accuracy_status must remain not_evaluated at promotion time.")

    # Independent fields require notes if set.
    if (
        review.independent_depth is not None or review.independent_undertone is not None
    ) and not review.independent_measurement_notes:
        reasons.append(
            "independent_* values require independent_measurement_notes documenting the evidence."
        )

    candidate = build_foundation_shade(review, staged)
    catalog_rows = (
        list(existing_catalog) if existing_catalog is not None else list(load_catalog())
    )
    collision = find_duplicate(candidate, catalog_rows)
    if collision is not None:
        reasons.append(
            "Duplicate of existing catalog entry "
            f"id={collision.id!r} ({collision.brand} / {collision.product} / "
            f"{collision.shade_name}). Existing NARS and other rows are preserved."
        )

    return reasons


def build_foundation_shade(
    review: ShadeReviewForm,
    staged: StagedFoundationShade,
) -> FoundationShade:
    """Build a live catalog row from review + staged provenance (no invented enums)."""
    catalog_id = suggest_catalog_id(review)
    provenance = (
        f"Human-verified against official source on {review.date_verified.isoformat()}. "
        f"Promoted from staged historical record {staged.id} "
        f"({staged.source_dataset}). "
        f"Historical retailer URL: {staged.historical_retailer_url}. "
        f"Original staging provenance retained for audit. "
        f"{staged.provenance_notes[:400]}"
    )[:800]

    uncertainty_bits = [
        review.uncertainty_notes or "",
        "Matching accuracy not evaluated — metadata verification is not match proof.",
        "Historical swatch hex/HSL were not imported as color measurements.",
    ]
    if staged.approx_hex:
        uncertainty_bits.append(
            f"Historical approx_hex for reference only (not used): {staged.approx_hex}."
        )
    uncertainty = " ".join(bit for bit in uncertainty_bits if bit).strip()[:800] or None

    notes = review.notes
    if review.reviewer_notes:
        extra = f"Reviewer: {review.reviewer_notes}"
        notes = f"{notes} {extra}".strip() if notes else extra
    if notes:
        notes = notes[:800]

    return FoundationShade(
        id=catalog_id,
        brand=review.confirmed_brand,
        product=review.confirmed_product,
        shade_name=review.confirmed_shade_name,
        shade_code=review.confirmed_shade_code,
        brand_shade_description=review.confirmed_brand_shade_description,
        brand_reported_depth=review.brand_reported_depth,
        brand_reported_undertone=review.brand_reported_undertone,
        independent_depth=review.independent_depth,
        independent_undertone=review.independent_undertone,
        independent_measurement_notes=review.independent_measurement_notes,
        source_url=review.official_source_url,
        date_verified=review.date_verified,
        verification_status="brand_verified",
        metadata_verification_status="source_checked",
        matching_accuracy_status="not_evaluated",
        provenance_notes=provenance,
        uncertainty_notes=uncertainty,
        notes=notes,
    )


def promote_reviewed_shade(
    review: ShadeReviewForm,
    *,
    staging_path: Path,
    catalog_file: Optional[Path] = None,
    dry_run: bool = False,
) -> PromotionResult:
    """
    Validate review gates and optionally append to foundation_catalog.json.

    Never modifies the staging file's eligibility flags.
    """
    from app.data.catalog_repository import _load_raw_shades, _validate_and_dedupe

    manifest = load_staging_manifest(staging_path)
    staged = find_staged_by_id(manifest.shades, review.staged_id)

    if catalog_file is not None:
        existing = _validate_and_dedupe(_load_raw_shades(catalog_file))
    else:
        existing = list(load_catalog())

    reasons = collect_rejection_reasons(review, staged, existing_catalog=existing)

    if reasons:
        return PromotionResult(
            promoted=False,
            rejection_reasons=reasons,
            message="Promotion rejected.",
        )

    assert staged is not None
    shade = build_foundation_shade(review, staged)

    if dry_run:
        return PromotionResult(
            promoted=False,
            catalog_id=shade.id,
            rejection_reasons=[],
            message=(
                f"Dry run OK — would promote as id={shade.id!r}, "
                f"recommendation_eligible={shade.recommendation_eligible}."
            ),
        )

    try:
        append_shade_to_catalog(shade, path=catalog_file)
    except CatalogDataError as exc:
        return PromotionResult(
            promoted=False,
            catalog_id=shade.id,
            rejection_reasons=[str(exc)],
            message="Promotion rejected while writing catalog.",
        )

    return PromotionResult(
        promoted=True,
        catalog_id=shade.id,
        rejection_reasons=[],
        message=(
            f"Promoted {shade.id!r} into catalog. "
            f"recommendation_eligible={shade.recommendation_eligible}. "
            "matching_accuracy_status remains not_evaluated."
        ),
    )


def load_review_form(path: Path) -> ShadeReviewForm:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    # Allow template helper keys without breaking validation.
    payload.pop("_warnings", None)
    payload.pop("_historical_snapshot", None)
    return ShadeReviewForm.model_validate(payload)


def write_review_template(shade: StagedFoundationShade, output_path: Path) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(build_review_template(shade), indent=2) + "\n",
        encoding="utf-8",
    )
    return output_path
