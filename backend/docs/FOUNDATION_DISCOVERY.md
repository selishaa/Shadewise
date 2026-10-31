# Foundation discovery API (Milestone C.2)

Search the **historical staging** dataset (The Pudding import) without mixing it into verified recommendations.

| Endpoint | Purpose |
|----------|---------|
| `GET /api/discover/shades` | Paginated search |
| `GET /api/discover/shades/{staged_id}` | One historical row |
| `GET /api/discover/brands` | Brand list + counts |
| `GET /api/catalog` | **Verified / demo live catalog** (unchanged) |
| `POST /api/match-shades` | Matcher on **live catalog only** (unchanged) |

Every discovery item has:

- `data_label`: `historical_unverified`
- `recommendation_eligible`: **false**
- `availability_note` about possibly outdated listings
- `approx_swatch.warning` if hex/HSL is present (uncalibrated — not a measurement)

## Prerequisites

Staging file must exist:

```bash
python -m scripts.import_pudding_shades \
  --input app/data/external/pudding/allShades.csv \
  --output app/data/staging/pudding_all_shades.json
```

Then start the API and open **http://127.0.0.1:8000/docs**.

## Example searches in `/docs`

1. Open **GET `/api/discover/shades`** → Try it out.  
2. Examples:
   - `brand` = `Maybelline`, `page_size` = `10`
   - `brand` = `Fenty`, `shade` = `100`
   - `q` = `Punjab`, `sort` = `product`
   - `page` = `2`, `page_size` = `20` (never dumps all 6,806 by default)
3. Compare with **GET `/api/catalog?brand=NARS`** — only the five verified live NARS rows, not the historical set.

Default `page_size` is **20** (max **100**).
