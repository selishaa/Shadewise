# Catalog verification workflow (staged → live)

Use this after importing The Pudding data into staging (`docs/PUDDING_IMPORT.md`).

**Nothing is recommendation-eligible until you promote a human-reviewed row.**
Staging imports alone never become matcher candidates.

## 1. Search historical records (exact match)

From `backend/`:

```bash
python -m scripts.review_staged_shade search \
  --brand Maybelline \
  --product "Fit Me Matte + Poreless Liquid Foundation" \
  --shade-code 110
```

Also: `--shade-name "Porcelain"`. At least one filter is required. Matching is **exact** (case-insensitive), not substring.

## 2. Inspect one staged shade

```bash
python -m scripts.review_staged_shade show --id <staged-id>
```

You will see historical metadata, retailer URL, and **warnings** that approx hex/HSL are uncalibrated swatches — not measurements.

## 3. Verify a shade (human steps)

1. Open the **current official brand product page** in your browser (do not scrape).
2. Confirm the shade still exists (availability).
3. Copy exact brand, product, shade name/code, and description from that page.
4. Set depth/undertone **only** if the brand clearly states them; otherwise leave `null`.
5. Leave all `independent_*` fields `null` unless you have documented wear/lab evidence.
6. Keep `matching_accuracy_status` = `not_evaluated`.

Generate a review template:

```bash
python -m scripts.review_staged_shade template \
  --id <staged-id> \
  --out app/data/staging/reviews/my-shade-review.json
```

Edit the JSON:

- `official_source_url` → real official URL  
- `confirm_identity_matches_official_page` → `true`  
- `confirm_source_checked` → `true`  
- `availability_confirmed` → `true` (required; discontinued stays out)  
- Fill `confirmed_*` fields from the live page  

The template embeds `_historical_snapshot` for audit; promotion ignores helper keys.

## 4. Promote one verified record

Dry run first:

```bash
python -m scripts.review_staged_shade promote \
  --review app/data/staging/reviews/my-shade-review.json \
  --dry-run
```

Write to the live catalog only when ready:

```bash
python -m scripts.review_staged_shade promote \
  --review app/data/staging/reviews/my-shade-review.json \
  --i-confirm-promotion
```

Promotion is rejected if confirms are false, the URL is still a placeholder, availability is unconfirmed, or the shade would duplicate an existing catalog row (including your five NARS records).

After a successful promote:

- Live row: `brand_verified` + `source_checked` + `not_evaluated`  
- May become `recommendation_eligible` (metadata trust only — **not** match proof)  
- Staging file is unchanged and remains ineligible  

## What never happens automatically

- No scraping  
- No inventing depth/undertone/hex measurements  
- No auto-promotion of the 6,806 historical rows  
- No matcher or frontend changes in this workflow  
