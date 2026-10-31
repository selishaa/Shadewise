"""Milestone B / B.1 — foundation catalog loading, validation, filters, eligibility."""

import json
from datetime import date
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.data import catalog_repository
from app.data.catalog_repository import (
    CatalogDataError,
    get_illustrative_catalog_products,
    list_shades,
    load_catalog,
    load_collection_template,
    recommendation_eligible_shades,
    reload_catalog,
)
from app.models.catalog import FoundationShade, RECOMMENDATION_ELIGIBLE_STATUSES


@pytest.fixture(autouse=True)
def _clear_catalog_cache():
    load_catalog.cache_clear()
    yield
    load_catalog.cache_clear()


def test_catalog_loads_demo_dataset():
    rows = reload_catalog()
    assert len(rows) >= 6
    assert all(isinstance(row, FoundationShade) for row in rows)
    demo_rows = [row for row in rows if row.brand == "ShadeWise Demo"]
    assert len(demo_rows) >= 6


def test_catalog_includes_five_nars_light_reflecting_shades():
    rows = reload_catalog()
    nars = [
        row
        for row in rows
        if row.brand == "NARS" and row.product == "Light Reflecting Foundation"
    ]
    assert len(nars) == 5
    by_name = {row.shade_name: row for row in nars}
    assert set(by_name) == {"Fiji", "Punjab", "Patagonia", "Santa Fe", "Stromboli"}

    fiji = by_name["Fiji"]
    assert fiji.shade_code == "L5"
    assert fiji.brand_reported_undertone == "warm"
    # "Light to medium" is not a single enum value — must stay null, wording preserved.
    assert fiji.brand_reported_depth is None
    assert "Light to medium" in (fiji.brand_shade_description or "")
    assert fiji.matching_accuracy_status == "not_evaluated"
    assert fiji.independent_depth is None
    assert fiji.independent_undertone is None
    assert fiji.verification_status == "brand_verified"
    assert fiji.metadata_verification_status == "source_checked"
    assert fiji.recommendation_eligible is True

    punjab = by_name["Punjab"]
    assert punjab.shade_code == "M1"
    assert punjab.brand_reported_depth == "medium"
    assert punjab.brand_reported_undertone == "warm"
    assert "Golden" in (punjab.brand_shade_description or "")

    patagonia = by_name["Patagonia"]
    assert patagonia.shade_code == "M1.2"
    assert patagonia.brand_reported_depth == "medium"
    assert patagonia.brand_reported_undertone == "neutral"
    assert "Light peach" in (patagonia.brand_shade_description or "")

    santa_fe = by_name["Santa Fe"]
    assert santa_fe.shade_code == "M2"
    assert santa_fe.brand_reported_depth == "medium"
    assert santa_fe.brand_reported_undertone == "neutral"

    stromboli = by_name["Stromboli"]
    assert stromboli.shade_code == "M3"
    assert stromboli.brand_reported_depth == "medium"
    assert stromboli.brand_reported_undertone == "warm"
    assert "Yellow" in (stromboli.brand_shade_description or "")

    for row in nars:
        assert row.matching_accuracy_status == "not_evaluated"
        assert row.independent_measurement_notes is None
        assert row.recommendation_eligible is True


def test_api_catalog_includes_nars_and_eligibility_filter(client):
    nars_resp = client.get("/api/catalog", params={"brand": "NARS"})
    assert nars_resp.status_code == 200
    nars_body = nars_resp.json()
    assert nars_body["total"] == 5
    assert nars_body["recommendation_eligible_count"] == 5

    eligible_resp = client.get(
        "/api/catalog",
        params={"brand": "NARS", "recommendation_eligible_only": True},
    )
    assert eligible_resp.status_code == 200
    eligible_body = eligible_resp.json()
    assert eligible_body["total"] == 5
    assert all(item["recommendation_eligible"] is True for item in eligible_body["items"])
    assert {item["shade_name"] for item in eligible_body["items"]} == {
        "Fiji",
        "Punjab",
        "Patagonia",
        "Santa Fe",
        "Stromboli",
    }


def test_catalog_validation_rejects_missing_required_fields():
    with pytest.raises(ValidationError):
        FoundationShade.model_validate(
            {
                "id": "x",
                "brand": "ShadeWise Demo",
                "product": "Test",
                "shade_name": "1",
                # missing verification_status, metadata_verification_status, provenance
            }
        )


def test_catalog_allows_missing_depth_and_undertone():
    shade = FoundationShade.model_validate(
        {
            "id": "missing-axes",
            "brand": "ShadeWise Demo",
            "product": "Studio Foundation",
            "shade_name": "999",
            "verification_status": "estimated",
            "metadata_verification_status": "unreviewed",
            "matching_accuracy_status": "not_evaluated",
            "provenance_notes": "Incomplete demo row for tests.",
            "brand_reported_depth": None,
            "brand_reported_undertone": None,
        }
    )
    assert shade.brand_reported_depth is None
    assert shade.brand_reported_undertone is None
    assert shade.independent_depth is None
    assert shade.recommendation_eligible is False


def test_brand_vs_independent_fields_stay_separate():
    shade = FoundationShade.model_validate(
        {
            "id": "split-axes",
            "brand": "ShadeWise Demo",
            "product": "Studio Foundation",
            "shade_name": "Split",
            "verification_status": "independently_measured",
            "metadata_verification_status": "source_checked",
            "matching_accuracy_status": "not_evaluated",
            "provenance_notes": "Test separation of brand vs independent labels.",
            "brand_reported_depth": "light",
            "brand_reported_undertone": "warm",
            "independent_depth": "medium",
            "independent_undertone": "neutral",
            "independent_measurement_notes": "Daylight jawline check (test only).",
        }
    )
    assert shade.brand_reported_depth == "light"
    assert shade.independent_depth == "medium"
    assert shade.brand_reported_undertone != shade.independent_undertone


def test_filter_by_brand_product_shade(client):
    response = client.get(
        "/api/catalog",
        params={
            "brand": "shadewise demo",
            "product": "Everyday Soft Matte Foundation",
            "shade": "Light 2 Cool",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["shade_name"] == "Light 2 Cool"


def test_filter_unknown_brand_returns_empty(client):
    response = client.get("/api/catalog", params={"brand": "Not A Real Brand"})
    assert response.status_code == 200
    assert response.json()["total"] == 0
    assert response.json()["items"] == []


def test_duplicate_id_raises(tmp_path: Path, monkeypatch):
    path = tmp_path / "dup_id.json"
    path.write_text(
        json.dumps(
            {
                "shades": [
                    {
                        "id": "same",
                        "brand": "ShadeWise Demo",
                        "product": "A",
                        "shade_name": "1",
                        "verification_status": "illustrative",
                        "metadata_verification_status": "illustrative",
                        "provenance_notes": "demo",
                    },
                    {
                        "id": "same",
                        "brand": "ShadeWise Demo",
                        "product": "B",
                        "shade_name": "2",
                        "verification_status": "illustrative",
                        "metadata_verification_status": "illustrative",
                        "provenance_notes": "demo",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(CatalogDataError, match="Duplicate catalog id"):
        catalog_repository._validate_and_dedupe(
            catalog_repository._load_raw_shades(path)
        )


def test_duplicate_shade_identity_raises(tmp_path: Path, monkeypatch):
    path = tmp_path / "dup_key.json"
    path.write_text(
        json.dumps(
            {
                "shades": [
                    {
                        "id": "a",
                        "brand": "ShadeWise Demo",
                        "product": "Everyday Soft Matte Foundation",
                        "shade_name": "Light 2 Cool",
                        "shade_code": "L2C",
                        "verification_status": "illustrative",
                        "metadata_verification_status": "illustrative",
                        "provenance_notes": "demo",
                        "brand_reported_depth": "light",
                        "brand_reported_undertone": "cool",
                    },
                    {
                        "id": "b",
                        "brand": "shadewise demo",
                        "product": "everyday soft matte foundation",
                        "shade_name": "light 2 cool",
                        "shade_code": "l2c",
                        "verification_status": "illustrative",
                        "metadata_verification_status": "illustrative",
                        "provenance_notes": "demo",
                        "brand_reported_depth": "light",
                        "brand_reported_undertone": "cool",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(CatalogDataError, match="Duplicate shade identity"):
        catalog_repository._validate_and_dedupe(
            catalog_repository._load_raw_shades(path)
        )


def test_recommendation_eligible_excludes_illustrative_estimated_unreviewed():
    eligible = recommendation_eligible_shades()
    # eligibility property is source of truth for API filter
    eligible = [row for row in load_catalog() if row.recommendation_eligible]
    assert eligible
    assert all(
        row.verification_status in RECOMMENDATION_ELIGIBLE_STATUSES for row in eligible
    )
    assert all(row.metadata_verification_status == "source_checked" for row in eligible)
    assert all(row.matching_accuracy_status != "insufficient_evidence" for row in eligible)
    assert all(row.verification_status != "illustrative" for row in eligible)
    assert all(row.verification_status != "estimated" for row in eligible)


def test_insufficient_matching_accuracy_blocks_eligibility():
    row = next(r for r in load_catalog() if r.id == "demo-independent-medium-neutral")
    assert row.verification_status == "independently_measured"
    assert row.metadata_verification_status == "source_checked"
    assert row.matching_accuracy_status == "insufficient_evidence"
    assert row.recommendation_eligible is False


def test_api_recommendation_eligible_only_filter(client):
    all_resp = client.get("/api/catalog")
    eligible_resp = client.get(
        "/api/catalog", params={"recommendation_eligible_only": True}
    )
    assert all_resp.status_code == 200
    assert eligible_resp.status_code == 200

    all_body = all_resp.json()
    eligible_body = eligible_resp.json()

    assert eligible_body["total"] == eligible_body["recommendation_eligible_count"]
    assert eligible_body["total"] < all_body["total"]
    assert all(item["recommendation_eligible"] is True for item in eligible_body["items"])


def test_illustrative_hints_never_include_verified_rows():
    hints = get_illustrative_catalog_products()
    assert hints
    assert all(h.data_status == "illustrative" for h in hints)
    illustrative_ids = {
        row.id for row in load_catalog() if row.verification_status == "illustrative"
    }
    assert all(h.id in illustrative_ids for h in hints)


def test_list_shades_helper_matches_api_filters():
    rows = list_shades(product="Sheer Glow Tint")
    assert rows
    assert all(r.product == "Sheer Glow Tint" for r in rows)


def test_date_verified_parses_iso():
    row = next(r for r in load_catalog() if r.id == "demo-brand-verified-light-cool")
    assert row.date_verified == date(2026, 10, 1)


def test_collection_template_loads_and_worksheet_validates():
    template = load_collection_template()
    assert "entry_template" in template
    assert "first_five_real_shades_worksheet" in template
    worksheet = template["first_five_real_shades_worksheet"]
    assert len(worksheet) == 5

    for stub in worksheet:
        shade = FoundationShade.model_validate(stub)
        assert shade.metadata_verification_status == "unreviewed"
        assert shade.matching_accuracy_status == "not_evaluated"
        assert shade.recommendation_eligible is False
        assert "REPLACE" in shade.shade_name or shade.shade_name.startswith("REPLACE")


def test_cross_brand_worksheet_c1a_is_unreviewed_and_balanced():
    """Milestone C.1a — collection stubs only; nothing verified or live yet."""
    template = load_collection_template()
    assert template.get("milestone") == "C.1a"
    refs = template["reference_product_pages"]
    assert "nars_light_reflecting_foundation" in refs
    assert "maybelline_fit_me_matte_poreless" in refs
    assert "fenty_pro_filtr_soft_matte" in refs
    assert "fentybeauty.com" in refs["fenty_pro_filtr_soft_matte"]

    plan = template["collection_plan"]
    assert plan["new_worksheet_slots"]["total_new_slots"] == 19
    assert plan["already_in_live_catalog"]["nars_light_reflecting"] == 5

    worksheet = template["cross_brand_shades_worksheet"]
    assert len(worksheet) == 19

    by_brand = {}
    for stub in worksheet:
        shade = FoundationShade.model_validate(stub)
        assert shade.metadata_verification_status == "unreviewed"
        assert shade.verification_status == "estimated"
        assert shade.matching_accuracy_status == "not_evaluated"
        assert shade.recommendation_eligible is False
        assert shade.independent_depth is None
        assert shade.independent_undertone is None
        assert "REPLACE" in shade.shade_name
        by_brand[shade.brand] = by_brand.get(shade.brand, 0) + 1

    assert by_brand["NARS"] == 3
    assert by_brand["Maybelline"] == 8
    assert by_brand["Fenty Beauty"] == 8

    # Live catalog must still contain the five existing NARS rows only (no worksheet paste yet).
    live = [r for r in reload_catalog() if r.brand == "NARS"]
    assert len(live) == 5
    assert all(r.shade_name != "REPLACE_WITH_EXACT_SHADE_NAME_FROM_PAGE" for r in live)


def test_unreviewed_real_brand_stub_not_eligible():
    shade = FoundationShade.model_validate(
        {
            "id": "nars-draft",
            "brand": "NARS",
            "product": "Light Reflecting Foundation",
            "shade_name": "Draft Shade",
            "source_url": (
                "https://www.narscosmetics.com/USA/"
                "light-reflecting%E2%84%A2-advanced-skincare-foundation/999NAC0000141.html"
            ),
            "verification_status": "estimated",
            "metadata_verification_status": "unreviewed",
            "matching_accuracy_status": "not_evaluated",
            "provenance_notes": "Draft only — not source_checked.",
        }
    )
    assert shade.recommendation_eligible is False
