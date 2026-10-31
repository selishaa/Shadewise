# Importing The Pudding foundation-names (Milestone C.1b)

## What this is

An **offline staging importer** for historical shade rows from:

https://github.com/the-pudding/data/tree/master/foundation-names

It does **not** update `foundation_catalog.json`, the matcher, or the frontend.

Every staged row is:

| Field | Value |
|-------|--------|
| `verification_status` | `estimated` |
| `metadata_verification_status` | `unreviewed` |
| `matching_accuracy_status` | `not_evaluated` |
| `recommendation_eligible` | `false` |
| `brand_reported_depth` / `undertone` | always `null` (not invented) |

Approximate `approx_hex` / HSL values are **uncalibrated swatch extractions**, not lab measurements.

## License & attribution

- Upstream repo license: **MIT** (© 2019 The Pudding) — see `app/data/external/pudding/LICENSE`
- Human summary: `app/data/external/pudding/ATTRIBUTION.md`
- MIT covers The Pudding’s compilation/scripts in that repo; it does **not** grant rights to rehost Ulta/Sephora swatch images or to treat brand trademarks as yours.

## One-time setup: get the CSV

1. Open the GitHub folder above in a browser.
2. Download `allShades.csv` (or use the raw URL in a browser “Save as…”).
3. Save it somewhere local, for example:

```text
backend/app/data/external/pudding/allShades.csv
```

Do not scrape Sephora/Ulta yourself for this milestone — use the published CSV.

## Run the importer

From `backend/` (with your venv active):

```bash
python -m scripts.import_pudding_shades \
  --input app/data/external/pudding/allShades.csv \
  --output app/data/staging/pudding_all_shades.json
```

Optional: `--omit-skipped-rows` for a smaller JSON (counts still appear in the report).

The command prints **imported / skipped / duplicates / incomplete** counts.

## Inspect NARS, Maybelline, and Fenty

```bash
python -m scripts.inspect_pudding_staging --brand NARS --limit 30
python -m scripts.inspect_pudding_staging --brand Maybelline --product "Fit Me"
python -m scripts.inspect_pudding_staging --brand Fenty --limit 30
python -m scripts.inspect_pudding_staging --brands-only
```

Notes from the feasibility study:

- **NARS** rows exist, but **Light Reflecting Foundation** is generally absent (2021 snapshot).
- **Maybelline Fit Me Matte + Poreless** appears under a similar product title.
- **Fenty** appears as `FENTY BEAUTY by Rihanna` with Pro Filt'r Soft Matte lines.

## How a human later verifies a staged record (before live catalog)

Use the guided CLI workflow in **`docs/CATALOG_VERIFICATION.md`**:

```bash
python -m scripts.review_staged_shade search --brand Maybelline --shade-code 110
python -m scripts.review_staged_shade show --id <staged-id>
python -m scripts.review_staged_shade template --id <staged-id> --out app/data/staging/reviews/draft.json
# edit draft.json, then:
python -m scripts.review_staged_shade promote --review ... --dry-run
python -m scripts.review_staged_shade promote --review ... --i-confirm-promotion
```

See also: `docs/CROSS_BRAND_DATA_WORKSHEET.md` and `docs/CATALOG_DATA_COLLECTION.md`.

## Safety checks built into the tool

- Refuses to write to a file named `foundation_catalog.json`
- Skips rows with no brand/product or no shade identity at all
- Deduplicates within one import on brand+product+code+name+hex+description
- Keeps the full original CSV fields under each row’s `raw` object
