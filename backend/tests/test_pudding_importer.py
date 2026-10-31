"""Milestone C.1b — offline The Pudding allShades staging importer."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.data.catalog_repository import reload_catalog
from app.services.pudding_importer import (
    filter_staged_shades,
    import_all_shades_csv,
    load_staging_manifest,
    row_to_staged,
)
from scripts.import_pudding_shades import main as import_main
from scripts.inspect_pudding_staging import main as inspect_main

FIXTURE = Path(__file__).parent / "fixtures" / "pudding_allShades_sample.csv"
LIVE_CATALOG = (
    Path(__file__).resolve().parents[1] / "app" / "data" / "foundation_catalog.json"
)


@pytest.fixture
def staging_path(tmp_path: Path) -> Path:
    return tmp_path / "pudding_staging.json"


def test_fixture_import_counts_and_safety_flags(staging_path: Path):
    manifest = import_all_shades_csv(FIXTURE, output_path=staging_path)

    report = manifest.report
    # 10 data rows in fixture: 7 imported, 1 duplicate, 2 skipped (missing product, no identity)
    assert report.imported == 7
    assert report.duplicates == 1
    assert report.skipped == 3  # duplicate + missing_brand_or_product + no_shade_identity
    assert report.skip_reasons["duplicate"] == 1
    assert report.skip_reasons["missing_brand_or_product"] == 1
    assert report.skip_reasons["no_shade_identity"] == 1
    assert report.incomplete >= 1

    assert staging_path.exists()
    assert all(s.verification_status == "estimated" for s in manifest.shades)
    assert all(s.metadata_verification_status == "unreviewed" for s in manifest.shades)
    assert all(s.matching_accuracy_status == "not_evaluated" for s in manifest.shades)
    assert all(s.recommendation_eligible is False for s in manifest.shades)
    assert all(s.brand_reported_depth is None for s in manifest.shades)
    assert all(s.brand_reported_undertone is None for s in manifest.shades)

    # Raw fields preserved for audit
    first = manifest.shades[0]
    assert "brand" in first.raw and "hex" in first.raw
    assert "MIT" in manifest.license_note or "MIT" in manifest.attribution
    assert "uncalibrated" in manifest.color_caveat.lower() or "swatch" in manifest.color_caveat.lower()


def test_hex_normalization_and_malformed_hex(staging_path: Path):
    manifest = import_all_shades_csv(FIXTURE, output_path=staging_path)
    by_code = {s.shade_code: s for s in manifest.shades if s.shade_code}

    assert by_code["145"].approx_hex == "#FFC8A3"  # leading # added
    broken = next(s for s in manifest.shades if s.shade_code == "Z1")
    assert broken.approx_hex is None
    assert "malformed_or_missing_hex" in broken.incomplete_flags
    # Still imported — identity existed; color just incomplete
    assert broken.shade_name == "Shade Z"


def test_fenty_missing_name_uses_code_not_invented(staging_path: Path):
    manifest = import_all_shades_csv(FIXTURE, output_path=staging_path)
    fenty = [s for s in manifest.shades if "fenty" in s.brand.casefold()]
    assert len(fenty) == 2
    for row in fenty:
        assert row.shade_name is None  # NA was not invented into a name
        assert row.shade_code in {"100", "145"}
        assert row.brand_shade_description is not None


def test_duplicate_nars_punjab_imported_once(staging_path: Path):
    manifest = import_all_shades_csv(FIXTURE, output_path=staging_path)
    punjab = [
        s
        for s in manifest.shades
        if s.shade_name == "Punjab" and s.brand == "NARS"
    ]
    assert len(punjab) == 1
    assert manifest.report.duplicates == 1


def test_filter_by_brand_product(staging_path: Path):
    manifest = import_all_shades_csv(FIXTURE, output_path=staging_path)
    maybelline = filter_staged_shades(manifest.shades, brand="maybelline", product="fit me")
    assert len(maybelline) == 3
    assert all("Maybelline" in s.brand for s in maybelline)

    fenty = filter_staged_shades(manifest.shades, brand="Fenty")
    assert len(fenty) == 2


def test_refuses_to_write_live_catalog_filename(tmp_path: Path):
    banned = tmp_path / "foundation_catalog.json"
    with pytest.raises(ValueError, match="foundation_catalog.json"):
        import_all_shades_csv(FIXTURE, output_path=banned)


def test_live_catalog_unchanged_by_import(staging_path: Path):
    before = LIVE_CATALOG.read_text(encoding="utf-8")
    import_all_shades_csv(FIXTURE, output_path=staging_path)
    after = LIVE_CATALOG.read_text(encoding="utf-8")
    assert before == after

    live = reload_catalog()
    nars = [r for r in live if r.brand == "NARS"]
    assert len(nars) == 5
    assert not any(r.id.startswith("pudding-") for r in live)


def test_load_staging_roundtrip(staging_path: Path):
    import_all_shades_csv(FIXTURE, output_path=staging_path)
    loaded = load_staging_manifest(staging_path)
    assert loaded.report.imported == 7
    assert staging_path.read_text(encoding="utf-8")
    payload = json.loads(staging_path.read_text(encoding="utf-8"))
    assert payload["shades"][0]["recommendation_eligible"] is False


def test_cli_import_and_inspect(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    out = tmp_path / "out.json"
    code = import_main(["--input", str(FIXTURE), "--output", str(out)])
    assert code == 0
    captured = capsys.readouterr().out
    assert "imported:" in captured.lower() or "imported" in captured.lower()

    code = inspect_main(
        ["--staging", str(out), "--brand", "Maybelline", "--product", "Fit Me", "--limit", "10"]
    )
    assert code == 0
    printed = capsys.readouterr().out
    assert "Maybelline" in printed
    assert "eligible=False" in printed or "eligible=false" in printed.lower()


def test_row_to_staged_does_not_infer_undertone():
    shade, reason, flags = row_to_staged(
        {
            "brand": "FENTY BEAUTY by Rihanna",
            "product": "Pro Filt'r Soft Matte Longwear Foundation",
            "url": "https://example.com",
            "description": "100 for very fair skin with cool pink undertones",
            "imgSrc": "",
            "imgAlt": "",
            "name": "NA",
            "specific": "100",
            "colorspace": "RGB",
            "hex": "#FFDEC3",
            "hue": "32",
            "sat": "0.4",
            "lightness": "0.88",
        },
        row_number=2,
        source_file="sample.csv",
        imported_at=datetime.now(timezone.utc),
    )
    assert reason is None
    assert shade is not None
    assert shade.brand_reported_undertone is None
    assert shade.brand_reported_depth is None
    assert "cool" in (shade.brand_shade_description or "").lower()
