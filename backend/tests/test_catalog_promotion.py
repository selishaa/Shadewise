"""Verification workflow: review gates + promote staged shade → live catalog."""

from __future__ import annotations

import json
import shutil
from datetime import date
from pathlib import Path

import pytest

from app.data.catalog_repository import load_catalog, reload_catalog
from app.models.review import ShadeReviewForm
from app.services.catalog_promotion import (
    build_review_template,
    collect_rejection_reasons,
    find_staged_by_id,
    find_staged_exact,
    load_review_form,
    promote_reviewed_shade,
    write_review_template,
)
from app.services.pudding_importer import import_all_shades_csv
from scripts.review_staged_shade import main as review_main

FIXTURE = Path(__file__).parent / "fixtures" / "pudding_allShades_sample.csv"
LIVE_CATALOG = (
    Path(__file__).resolve().parents[1] / "app" / "data" / "foundation_catalog.json"
)


@pytest.fixture
def staging_path(tmp_path: Path) -> Path:
    out = tmp_path / "staging.json"
    import_all_shades_csv(FIXTURE, output_path=out)
    return out


@pytest.fixture
def catalog_copy(tmp_path: Path) -> Path:
    """Working copy of the live catalog — never write the real file in tests."""
    dest = tmp_path / "foundation_catalog.json"
    shutil.copy(LIVE_CATALOG, dest)
    load_catalog.cache_clear()
    return dest


def _maybelline_110(staging_path: Path):
    from app.services.pudding_importer import load_staging_manifest

    shades = load_staging_manifest(staging_path).shades
    hits = find_staged_exact(
        shades,
        brand="Maybelline",
        product="Fit Me Matte + Poreless Liquid Foundation",
        shade_code="110",
    )
    assert len(hits) == 1
    return hits[0]


def _valid_review(staged_id: str, **overrides) -> ShadeReviewForm:
    payload = {
        "staged_id": staged_id,
        "official_source_url": "https://www.maybelline.com/face-makeup/foundation-makeup/fit-me-matte-poreless-foundation",
        "date_verified": date(2026, 10, 31),
        "confirm_identity_matches_official_page": True,
        "confirm_source_checked": True,
        "availability_confirmed": True,
        "confirmed_brand": "Maybelline",
        "confirmed_product": "Fit Me Matte + Poreless Foundation",
        "confirmed_shade_name": "Porcelain",
        "confirmed_shade_code": "110",
        "confirmed_brand_shade_description": "Porcelain 110",
        "brand_reported_depth": "fair",
        "brand_reported_undertone": "neutral",
        "independent_depth": None,
        "independent_undertone": None,
        "independent_measurement_notes": None,
        "matching_accuracy_status": "not_evaluated",
        "catalog_id": "maybelline-fitme-110-porcelain",
        "uncertainty_notes": "Depth/undertone from clear brand naming; still not wear-validated.",
        "notes": "Test promotion only.",
    }
    payload.update(overrides)
    return ShadeReviewForm.model_validate(payload)


def test_exact_search_brand_product_code(staging_path: Path):
    from app.services.pudding_importer import load_staging_manifest

    shades = load_staging_manifest(staging_path).shades
    hits = find_staged_exact(
        shades,
        brand="Maybelline",
        product="Fit Me Matte + Poreless Liquid Foundation",
        shade_code="110",
    )
    assert len(hits) == 1
    assert hits[0].shade_name == "Porcelain"

    # Substring must NOT match when using exact search.
    assert (
        find_staged_exact(
            shades,
            brand="Maybelline",
            product="Fit Me",  # not exact product title
        )
        == []
    )


def test_staging_never_recommendation_eligible(staging_path: Path):
    from app.services.pudding_importer import load_staging_manifest

    for shade in load_staging_manifest(staging_path).shades:
        assert shade.recommendation_eligible is False
        assert shade.metadata_verification_status == "unreviewed"


def test_reject_without_source_checked_confirm(staging_path: Path, catalog_copy: Path):
    staged = _maybelline_110(staging_path)
    review = _valid_review(staged.id, confirm_source_checked=False)
    result = promote_reviewed_shade(
        review, staging_path=staging_path, catalog_file=catalog_copy
    )
    assert result.promoted is False
    assert any("confirm_source_checked" in r for r in result.rejection_reasons)


def test_reject_without_availability_confirmed(staging_path: Path, catalog_copy: Path):
    staged = _maybelline_110(staging_path)
    review = _valid_review(staged.id, availability_confirmed=False)
    result = promote_reviewed_shade(
        review, staging_path=staging_path, catalog_file=catalog_copy
    )
    assert result.promoted is False
    assert any("availability_confirmed" in r for r in result.rejection_reasons)


def test_reject_placeholder_official_url(staging_path: Path, catalog_copy: Path):
    staged = _maybelline_110(staging_path)
    review = _valid_review(
        staged.id,
        official_source_url="REPLACE_WITH_CURRENT_OFFICIAL_BRAND_URL",
    )
    result = promote_reviewed_shade(
        review, staging_path=staging_path, catalog_file=catalog_copy
    )
    assert result.promoted is False
    assert any("placeholder" in r.lower() for r in result.rejection_reasons)


def test_reject_independent_without_notes(staging_path: Path, catalog_copy: Path):
    staged = _maybelline_110(staging_path)
    review = _valid_review(
        staged.id,
        independent_depth="fair",
        independent_measurement_notes=None,
    )
    reasons = collect_rejection_reasons(review, staged)
    assert any("independent_measurement_notes" in r for r in reasons)


def test_valid_promotion_writes_catalog_copy_only(
    staging_path: Path, catalog_copy: Path
):
    live_before = LIVE_CATALOG.read_text(encoding="utf-8")
    staged = _maybelline_110(staging_path)
    review = _valid_review(staged.id)

    dry = promote_reviewed_shade(
        review, staging_path=staging_path, catalog_file=catalog_copy, dry_run=True
    )
    assert dry.promoted is False
    assert "Dry run OK" in dry.message

    result = promote_reviewed_shade(
        review, staging_path=staging_path, catalog_file=catalog_copy
    )
    assert result.promoted is True
    assert result.catalog_id == "maybelline-fitme-110-porcelain"

    payload = json.loads(catalog_copy.read_text(encoding="utf-8"))
    promoted = next(s for s in payload["shades"] if s["id"] == result.catalog_id)
    assert promoted["verification_status"] == "brand_verified"
    assert promoted["metadata_verification_status"] == "source_checked"
    assert promoted["matching_accuracy_status"] == "not_evaluated"
    assert promoted["independent_depth"] is None
    assert "recommendation_eligible" not in promoted
    assert staged.id in promoted["provenance_notes"]
    assert promoted["source_url"].startswith("https://")

    # Live catalog file on disk must be untouched.
    assert LIVE_CATALOG.read_text(encoding="utf-8") == live_before

    # Staging remains ineligible.
    from app.services.pudding_importer import load_staging_manifest

    still = find_staged_by_id(load_staging_manifest(staging_path).shades, staged.id)
    assert still is not None
    assert still.recommendation_eligible is False


def test_duplicate_promotion_rejected(staging_path: Path, catalog_copy: Path):
    staged = _maybelline_110(staging_path)
    review = _valid_review(staged.id)
    first = promote_reviewed_shade(
        review, staging_path=staging_path, catalog_file=catalog_copy
    )
    assert first.promoted is True

    second = promote_reviewed_shade(
        review, staging_path=staging_path, catalog_file=catalog_copy
    )
    assert second.promoted is False
    assert any("Duplicate" in r or "duplicate" in r.lower() for r in second.rejection_reasons)


def test_preserve_existing_nars_on_collision(staging_path: Path, catalog_copy: Path):
    """Attempting to promote a shade that matches live NARS Punjab is blocked."""
    from app.services.pudding_importer import load_staging_manifest

    shades = load_staging_manifest(staging_path).shades
    punjab = find_staged_exact(shades, brand="NARS", shade_name="Punjab")[0]
    review = _valid_review(
        punjab.id,
        official_source_url="https://www.narscosmetics.com/USA/example",
        confirmed_brand="NARS",
        confirmed_product="Light Reflecting Foundation",
        confirmed_shade_name="Punjab",
        confirmed_shade_code="M1",
        catalog_id="nars-lrf-punjab-m1",  # same id as live
        brand_reported_depth="medium",
        brand_reported_undertone="warm",
    )
    result = promote_reviewed_shade(
        review, staging_path=staging_path, catalog_file=catalog_copy
    )
    assert result.promoted is False
    assert any("Duplicate" in r or "nars-lrf-punjab" in r for r in result.rejection_reasons)

    payload = json.loads(catalog_copy.read_text(encoding="utf-8"))
    nars = [s for s in payload["shades"] if s.get("brand") == "NARS"]
    assert len(nars) == 5


def test_review_template_and_cli(staging_path: Path, tmp_path: Path, catalog_copy: Path):
    staged = _maybelline_110(staging_path)
    template_path = tmp_path / "review.json"
    write_review_template(staged, template_path)
    raw = json.loads(template_path.read_text(encoding="utf-8"))
    assert raw["confirm_source_checked"] is False
    assert raw["availability_confirmed"] is False
    assert "_historical_snapshot" in raw
    assert raw["_historical_snapshot"]["approx_hex"] == staged.approx_hex

    # load_review_form strips helper keys
    raw["official_source_url"] = "https://www.maybelline.com/example"
    raw["confirm_identity_matches_official_page"] = True
    raw["confirm_source_checked"] = True
    raw["availability_confirmed"] = True
    raw["confirmed_shade_name"] = "Porcelain"
    raw["catalog_id"] = "maybelline-fitme-110-cli"
    template_path.write_text(json.dumps(raw), encoding="utf-8")
    form = load_review_form(template_path)
    assert form.confirm_source_checked is True

    # CLI search
    code = review_main(
        [
            "--staging",
            str(staging_path),
            "search",
            "--brand",
            "Maybelline",
            "--shade-code",
            "110",
        ]
    )
    assert code == 0

    # CLI refuses promote without explicit flag
    code = review_main(
        [
            "--staging",
            str(staging_path),
            "promote",
            "--review",
            str(template_path),
            "--catalog",
            str(catalog_copy),
        ]
    )
    assert code == 1


def test_template_defaults_do_not_pass_gates(staging_path: Path):
    staged = _maybelline_110(staging_path)
    template = build_review_template(staged)
    template.pop("_warnings", None)
    template.pop("_historical_snapshot", None)
    # confirmed_shade_name may be set from history, but confirms are false
    form = ShadeReviewForm.model_validate(template)
    reasons = collect_rejection_reasons(form, staged)
    assert len(reasons) >= 3
