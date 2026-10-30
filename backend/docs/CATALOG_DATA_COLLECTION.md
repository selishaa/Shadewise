# ShadeWise catalog data collection (Milestone B.1)

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

**Recommendation eligibility** (for a future matcher) requires:

1. `verification_status` is `brand_verified` or `independently_measured`  
2. `metadata_verification_status` is `source_checked`  
3. `matching_accuracy_status` is **not** `insufficient_evidence`  

Having `matching_accuracy_status: not_evaluated` is OK for being a *candidate*; it does **not** claim the match works.  
`wear_validated` is reserved for later evidence.

## Official reference pages (open in a browser — do not scrape)

- NARS Light Reflecting Foundation:  
  https://www.narscosmetics.com/USA/light-reflecting%E2%84%A2-advanced-skincare-foundation/999NAC0000141.html  
- Maybelline Fit Me Matte + Poreless:  
  https://www.maybelline.com/face-makeup/foundation-makeup/fit-me-matte-poreless-foundation  

## How to add your first five real shades (manual)

1. Open `app/data/catalog_entry_template.json`.  
2. Use the five stubs in `first_five_real_shades_worksheet` (2 NARS + 3 Maybelline slots).  
3. On each product page, pick a real shade and copy **exactly**:
   - shade name  
   - shade code (if shown)  
   - brand description (if shown)  
4. Set depth/undertone **only** if the brand labels them (e.g. “warm”, “cool”). Otherwise leave `null`.  
5. Leave all `independent_*` fields `null` until you do a real wear test.  
6. When the row matches the page: set  
   - `metadata_verification_status`: `source_checked`  
   - `date_verified`: today’s date (`YYYY-MM-DD`)  
   - `verification_status`: `brand_verified`  
   - `matching_accuracy_status`: keep `not_evaluated`  
7. Change each stub `id` to a unique slug (e.g. `nars-lrf-punjab`).  
8. Copy finished objects into `foundation_catalog.json` → `shades` array.  
9. From `backend/`: run `pytest -q` then restart the API.  
10. Inspect: `GET /api/catalog?brand=NARS` and `?recommendation_eligible_only=true`.

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
