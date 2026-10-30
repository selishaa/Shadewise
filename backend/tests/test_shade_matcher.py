"""Milestone C — deterministic foundation shade matcher."""

from __future__ import annotations

from typing import List

import pytest

from app.data.catalog_repository import load_catalog, reload_catalog
from app.models.catalog import FoundationShade
from app.models.matching import MatchShadeRequest
from app.services.shade_matcher import (
    find_current_shade,
    is_matcher_candidate,
    match_shades,
)


@pytest.fixture(autouse=True)
def _clear_catalog_cache():
    load_catalog.cache_clear()
    yield
    load_catalog.cache_clear()


@pytest.fixture
def catalog() -> List[FoundationShade]:
    return reload_catalog()


def _nars_request(**overrides) -> MatchShadeRequest:
    base = {
        "brand": "NARS",
        "product": "Light Reflecting Foundation",
        "shade_name": "Punjab",
        "depth_feedback": "correct",
        "undertone_issue": "too_warm",
    }
    base.update(overrides)
    return MatchShadeRequest(**base)


def test_correct_depth_but_too_warm(catalog):
    result = match_shades(_nars_request(), catalog)

    assert result.matched_current_shade_id == "nars-lrf-punjab-m1"
    assert result.no_match_reason is None
    assert 1 <= len(result.recommendations) <= 3

    ids = [r.catalog_id for r in result.recommendations]
    assert "nars-lrf-punjab-m1" not in ids
    assert "nars-lrf-stromboli-m3" not in ids  # also warm
    assert set(ids) <= {
        "nars-lrf-patagonia-m1-2",
        "nars-lrf-santa-fe-m2",
    }
    for rec in result.recommendations:
        assert "ShadeWise Demo" not in rec.brand
        assert "matching accuracy" in rec.evidence_status.lower()
        assert "not proof" in rec.evidence_status.lower()
        assert "%" not in rec.evidence_status


def test_too_cool_pink(catalog):
    result = match_shades(
        _nars_request(
            shade_name="Patagonia",
            undertone_issue="too_cool",
            depth_feedback="correct",
        ),
        catalog,
    )

    assert result.matched_current_shade_id == "nars-lrf-patagonia-m1-2"
    assert result.no_match_reason is None
    ids = [r.catalog_id for r in result.recommendations]
    assert "nars-lrf-patagonia-m1-2" not in ids
    # Prefer warmer medium shades; neutrals are also acceptable as softer shift.
    assert any(i in ids for i in ("nars-lrf-punjab-m1", "nars-lrf-stromboli-m3"))
    # Warm should rank above neutral; cool must never appear.
    first = next(s for s in catalog if s.id == ids[0])
    assert first.brand_reported_undertone == "warm"
    for rec in result.recommendations:
        shade = next(s for s in catalog if s.id == rec.catalog_id)
        assert shade.brand_reported_undertone != "cool"


def test_too_light(catalog):
    # Punjab is medium — need a deeper real catalog shade. None exist → no match.
    result = match_shades(
        _nars_request(depth_feedback="too_light", undertone_issue="none"),
        catalog,
    )
    assert result.recommendations == []
    assert result.no_match_reason is not None
    assert "No suitable" in result.no_match_reason or "depth" in result.no_match_reason.lower()


def test_too_dark(catalog):
    # Medium → need lighter classified shade. Fiji has null depth → not used.
    result = match_shades(
        _nars_request(depth_feedback="too_dark", undertone_issue="none"),
        catalog,
    )
    assert result.recommendations == []
    assert result.no_match_reason is not None


def test_missing_depth_on_current_shade_fiji(catalog):
    result = match_shades(
        _nars_request(
            shade_name="Fiji",
            depth_feedback="correct",
            undertone_issue="too_warm",
        ),
        catalog,
    )
    assert result.matched_current_shade_id == "nars-lrf-fiji-l5"
    assert result.recommendations == []
    assert "no normalized depth" in (result.no_match_reason or "").lower()


def test_missing_undertone_blocks_same_undertone_filter(catalog):
    # Synthetic: take Punjab and blank undertone for the "current" role via a clone list.
    rows = list(catalog)
    punjab = next(s for s in rows if s.id == "nars-lrf-punjab-m1")
    mutated = punjab.model_copy(
        update={"brand_reported_undertone": None, "independent_undertone": None}
    )
    patched = [mutated if s.id == punjab.id else s for s in rows]

    result = match_shades(
        _nars_request(depth_feedback="correct", undertone_issue="none"),
        patched,
    )
    assert result.recommendations == []
    assert "undertone" in (result.no_match_reason or "").lower()


def test_unrecognized_current_shade(catalog):
    result = match_shades(
        _nars_request(shade_name="Not A Real Shade", depth_feedback="correct"),
        catalog,
    )
    assert result.matched_current_shade_id is None
    assert result.recommendations == []
    assert "not found" in (result.no_match_reason or "").lower()


def test_no_suitable_candidates_when_signals_empty(catalog):
    result = match_shades(
        MatchShadeRequest(
            brand="NARS",
            shade_name="Punjab",
            depth_feedback="unsure",
            undertone_issue="unsure",
        ),
        catalog,
    )
    assert result.recommendations == []
    assert "Need at least one clear" in (result.no_match_reason or "")


def test_excludes_fictional_shadewise_demo_products(catalog):
    # Even though two Demo rows are recommendation_eligible, matcher must never return them.
    eligible_demos = [
        s
        for s in catalog
        if s.brand == "ShadeWise Demo" and s.recommendation_eligible
    ]
    assert len(eligible_demos) >= 1

    result = match_shades(_nars_request(), catalog)
    for rec in result.recommendations:
        assert rec.brand != "ShadeWise Demo"
        assert not rec.catalog_id.startswith("demo-")

    for shade in catalog:
        if shade.brand == "ShadeWise Demo":
            assert is_matcher_candidate(shade) is False


def test_deterministic_ranking(catalog):
    first = match_shades(_nars_request(), catalog)
    second = match_shades(_nars_request(), catalog)
    assert [r.catalog_id for r in first.recommendations] == [
        r.catalog_id for r in second.recommendations
    ]
    # Stable alphabetical among equal scores: Patagonia before Santa Fe.
    if len(first.recommendations) >= 2:
        assert first.recommendations[0].catalog_id == "nars-lrf-patagonia-m1-2"
        assert first.recommendations[1].catalog_id == "nars-lrf-santa-fe-m2"


def test_never_invents_catalog_products(catalog):
    result = match_shades(_nars_request(), catalog)
    known_ids = {s.id for s in catalog}
    for rec in result.recommendations:
        assert rec.catalog_id in known_ids
        source = next(s for s in catalog if s.id == rec.catalog_id)
        assert rec.brand == source.brand
        assert rec.product == source.product
        assert rec.shade_name == source.shade_name


def test_undertone_only_without_depth_feedback_can_skip_fiji_depth(catalog):
    """Fiji has no depth; with depth=unsure and too_warm, cooler mediums may still appear."""
    result = match_shades(
        _nars_request(
            shade_name="Fiji",
            depth_feedback="unsure",
            undertone_issue="too_warm",
        ),
        catalog,
    )
    assert result.matched_current_shade_id == "nars-lrf-fiji-l5"
    assert result.no_match_reason is None
    ids = {r.catalog_id for r in result.recommendations}
    assert ids <= {
        "nars-lrf-patagonia-m1-2",
        "nars-lrf-santa-fe-m2",
    }
    assert "nars-lrf-fiji-l5" not in ids


def test_find_current_shade_by_code(catalog):
    req = MatchShadeRequest(
        brand="NARS",
        product="Light Reflecting Foundation",
        shade_code="M1",
        depth_feedback="correct",
        undertone_issue="too_warm",
    )
    found = find_current_shade(catalog, req)
    assert found is not None
    assert found.shade_name == "Punjab"


def test_match_shades_api_endpoint_no_openai(client, catalog):
    response = client.post(
        "/api/match-shades",
        json={
            "brand": "NARS",
            "product": "Light Reflecting Foundation",
            "shade_name": "Punjab",
            "depth_feedback": "correct",
            "undertone_issue": "too_warm",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["matched_current_shade_id"] == "nars-lrf-punjab-m1"
    assert len(data["recommendations"]) >= 1
    assert data["no_match_reason"] is None
    assert any("not proof" in lim.lower() or "not" in lim.lower() for lim in data["global_limitations"])


def test_root_lists_match_endpoint(client):
    assert client.get("/").json()["match_shades"] == "/api/match-shades"
