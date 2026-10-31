# ShadeWise catalog data collection

## What we are collecting

A **catalog row** is one foundation shade with:

- Identity: brand, product, shade name, optional shade code  
- Brand text: description copied from the brand (not invented)  
- Brand-reported depth / undertone (only if the brand says so)  
- Optional independent measurements (separate fields — usually empty at first)  
- Source URL + date you checked it  
- Two different “verified” flags (see below)

## Two kinds of verification (important)

| Field | Question it answers | Safe default for new real shades |
|-------|---------------------|----------------------------------|
| `metadata_verification_status` | Did a human check this row against the official page/packaging? | `unreviewed` → then `source_checked` |
| `matching_accuracy_status` | Do we have evidence this shade is a good *match recommendation*? | `not_evaluated` |

Also set `verification_status`:

- `brand_verified` — metadata copied from brand and `source_checked`  
- `independently_measured` — you also filled independent_* fields from real testing  
- `estimated` — draft / incomplete  
- `illustrative` — fictional demo only  

**Recommendation eligibility** (matcher candidates) requires:

1. `verification_status` is `brand_verified` or `independently_measured`  
2. `metadata_verification_status` is `source_checked`  
3. `matching_accuracy_status` is **not** `insufficient_evidence`  

Having `matching_accuracy_status: not_evaluated` is OK for being a *candidate*; it does **not** claim the match works.  
`wear_validated` is reserved for later evidence.

**Metadata verification ≠ matching accuracy.**

## Official reference pages (open in a browser — do not scrape)

- NARS Light Reflecting Foundation:  
  https://www.narscosmetics.com/USA/light-reflecting%E2%84%A2-advanced-skincare-foundation/999NAC0000141.html  
- Maybelline Fit Me Matte + Poreless:  
  https://www.maybelline.com/face-makeup/foundation-makeup/fit-me-matte-poreless-foundation  
- Fenty Beauty Pro Filt'r Soft Matte Longwear Foundation:  
  https://fentybeauty.com/products/pro-filtr-soft-matte-longwear-foundation  

## Milestone C.1a — cross-brand worksheet

Use the beginner guide and blank table here:

- **`docs/CROSS_BRAND_DATA_WORKSHEET.md`**
- JSON stubs: `app/data/catalog_entry_template.json` → `cross_brand_shades_worksheet`

Plan: keep 5 existing NARS rows; collect **3 more NARS** + **8 Maybelline** + **8 Fenty** (~24 real shades).

Ambiguous bands (`light-medium`, `medium-deep`, `light to medium`) → leave `brand_reported_depth` **null**.

## Milestone C.1b — historical staging import (The Pudding)

Offline importer for The Pudding `foundation-names` / `allShades.csv` writes **staging JSON only**.  
It never merges into `foundation_catalog.json` and never marks rows recommendation-eligible.

See **`docs/PUDDING_IMPORT.md`**.

## Milestone C.2 — discovery search API

Read-only search over staging: **`docs/FOUNDATION_DISCOVERY.md`**  
(`GET /api/discover/shades` — separate from verified `/api/catalog`).

## How to add shades to the live catalog (manual promotion)

1. Finish and review the C.1a worksheet.  
2. Copy finished objects into `foundation_catalog.json` → `shades` array (strip worksheet-only fields like `brand_depth_band`).  
3. From `backend/`: run `pytest -q` then restart the API.  
4. Inspect: `GET /api/catalog?brand=NARS` (and Maybelline / Fenty) and `?recommendation_eligible_only=true`.

## What still needs a human (we will not invent this)

- Exact shade names/codes on those pages  
- Exact brand descriptions  
- Whether depth/undertone are brand-stated or unknown  
- Whether any independent wear observation is true  
- Promoting `matching_accuracy_status` beyond `not_evaluated`  

## Rules

- No scraping bots.  
- No guessing Lab/RGB values.  
- No marking `source_checked` or `brand_verified` without opening the source.  
- Demo “ShadeWise Demo” rows stay for tests; real brands are separate rows.  
- Preserve the five existing NARS records when expanding.  
