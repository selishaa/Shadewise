"""Milestone C.2 — historical foundation discovery API."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.data.catalog_repository import reload_catalog
from app.data.staging_repository import (
    paginate,
    search_staged_shades,
    set_staging_path_override,
    sort_staged_shades,
)
from app.services.pudding_importer import import_all_shades_csv, load_staging_manifest

FIXTURE = Path(__file__).parent / "fixtures" / "pudding_allShades_sample.csv"


@pytest.fixture
def staged_file(tmp_path: Path):
    path = tmp_path / "pudding_staging.json"
    import_all_shades_csv(FIXTURE, output_path=path)
    set_staging_path_override(path)
    yield path
    set_staging_path_override(None)


def test_search_by_brand_and_shade_code(staged_file: Path, client):
    response = client.get(
        "/api/discover/shades",
        params={"brand": "Maybelline", "shade": "110", "page_size": 10},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_matches"] == 1
    assert len(data["items"]) == 1
    item = data["items"][0]
    assert item["brand"] == "Maybelline"
    assert item["shade_code"] == "110"
    assert item["shade_name"] == "Porcelain"
    assert item["recommendation_eligible"] is False
    assert item["data_label"] == "historical_unverified"
    assert item["verification_status"] == "estimated"
    assert item["metadata_verification_status"] == "unreviewed"
    assert "outdated" in item["availability_note"].lower()
    assert "disclaimer" in data
    assert "uncalibrated" in data["color_caveat"].lower() or "swatch" in data["color_caveat"].lower()


def test_pagination_does_not_dump_all(staged_file: Path, client):
    page1 = client.get("/api/discover/shades", params={"page": 1, "page_size": 2}).json()
    page2 = client.get("/api/discover/shades", params={"page": 2, "page_size": 2}).json()

    assert page1["page_size"] == 2
    assert page1["total_matches"] == 7  # fixture imported count
    assert page1["total_pages"] == 4
    assert len(page1["items"]) == 2
    assert len(page2["items"]) == 2
    ids1 = {i["id"] for i in page1["items"]}
    ids2 = {i["id"] for i in page2["items"]}
    assert ids1.isdisjoint(ids2)


def test_page_size_capped(staged_file: Path, client):
    response = client.get("/api/discover/shades", params={"page_size": 500})
    assert response.status_code == 422  # pydantic/query le=100


def test_missing_shade_name_still_returned(staged_file: Path, client):
    response = client.get(
        "/api/discover/shades",
        params={"brand": "Fenty", "shade": "100"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_matches"] == 1
    item = data["items"][0]
    assert item["shade_name"] is None
    assert item["shade_code"] == "100"
    assert "missing_shade_name" in item["incomplete_flags"]
    assert item["approx_swatch"] is not None
    assert "NOT a calibrated" in item["approx_swatch"]["warning"]


def test_malformed_hex_omits_or_warns_without_claiming_accuracy(
    staged_file: Path, client
):
    response = client.get(
        "/api/discover/shades",
        params={"brand": "Color Broken", "shade": "Z1"},
    )
    assert response.status_code == 200
    item = response.json()["items"][0]
    # hex was malformed on import → approx_hex null; HSL may still exist
    if item["approx_swatch"] is not None:
        assert item["approx_swatch"]["hex"] is None
        assert "warning" in item["approx_swatch"]
    assert item["recommendation_eligible"] is False


def test_sort_by_shade_code(staged_file: Path, client):
    response = client.get(
        "/api/discover/shades",
        params={"brand": "Maybelline", "sort": "shade_code", "order": "asc"},
    )
    codes = [i["shade_code"] for i in response.json()["items"]]
    assert codes == sorted(codes, key=lambda c: (c or "").casefold())


def test_discover_detail_and_brands(staged_file: Path, client):
    listing = client.get(
        "/api/discover/shades", params={"brand": "NARS", "shade": "Punjab"}
    ).json()
    staged_id = listing["items"][0]["id"]

    detail = client.get(f"/api/discover/shades/{staged_id}")
    assert detail.status_code == 200
    body = detail.json()
    assert body["id"] == staged_id
    assert body["recommendation_eligible"] is False

    missing = client.get("/api/discover/shades/does-not-exist")
    assert missing.status_code == 404

    brands = client.get("/api/discover/brands", params={"q": "Maybelline"}).json()
    assert brands["total_brands"] >= 1
    assert any(b["brand"] == "Maybelline" for b in brands["items"])


def test_discovery_separate_from_verified_catalog(staged_file: Path, client):
    discover = client.get("/api/discover/shades", params={"brand": "NARS"}).json()
    catalog = client.get("/api/catalog", params={"brand": "NARS"}).json()

    # Fixture NARS is Sheer Glow Punjab (historical). Live catalog has 5 LRF shades.
    assert discover["total_matches"] >= 1
    assert all(i["data_label"] == "historical_unverified" for i in discover["items"])
    assert all(i["recommendation_eligible"] is False for i in discover["items"])

    assert catalog["total"] == 5
    live = reload_catalog()
    assert all(r.product == "Light Reflecting Foundation" for r in live if r.brand == "NARS")
    assert not any(r.id.startswith("pudding-") for r in live)


def test_root_lists_discover(client, staged_file: Path):
    root = client.get("/").json()
    assert root["discover_shades"] == "/api/discover/shades"
    assert root["catalog"] == "/api/catalog"


def test_503_without_staging_file(client, tmp_path: Path):
    set_staging_path_override(tmp_path / "missing.json")
    try:
        response = client.get("/api/discover/shades")
        assert response.status_code == 503
    finally:
        set_staging_path_override(None)


def test_search_helpers_unit(staged_file: Path):
    shades = load_staging_manifest(staged_file).shades
    found = search_staged_shades(shades, q="porcelain")
    assert len(found) == 1
    ordered = sort_staged_shades(found, sort="id", order="asc")
    page, total, pages = paginate(ordered, page=1, page_size=10)
    assert total == 1 and pages == 1 and len(page) == 1


def test_suggest_ranks_prefix_brands_and_caps_results(staged_file: Path, client):
    response = client.get("/api/discover/suggest", params={"q": "May", "limit": 5})
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "May"
    assert len(data["brands"]) <= 5
    assert len(data["products"]) <= 5
    assert len(data["shades"]) <= 5
    assert any(b["brand"] == "Maybelline" for b in data["brands"])
    # Prefix brand match preferred
    assert data["brands"][0]["brand"] == "Maybelline"
    assert data["brands"][0]["match_type"] == "prefix"


def test_suggest_finds_fenty_and_nars(staged_file: Path, client):
    fenty = client.get("/api/discover/suggest", params={"q": "Fen"}).json()
    assert any("Fenty" in b["brand"] or "FENTY" in b["brand"] for b in fenty["brands"])

    nars = client.get("/api/discover/suggest", params={"q": "NAR"}).json()
    assert any(b["brand"] == "NARS" for b in nars["brands"])


def test_products_for_brand(staged_file: Path, client):
    response = client.get(
        "/api/discover/products",
        params={"brand": "Maybelline"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_products"] >= 1
    assert all(p["brand"] == "Maybelline" for p in data["items"])

    missing = client.get("/api/discover/products", params={"brand": "NotARealBrand"})
    assert missing.status_code == 404
