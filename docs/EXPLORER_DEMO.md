# ShadeWise consumer demo (unified Find My Shade)

## Local URLs

| Page | URL |
|------|-----|
| Homepage | http://localhost:3000 |
| **Find My Shade (primary)** | http://localhost:3000/find-your-shade |
| Shade archive (secondary) | http://localhost:3000/explore |
| Internal NARS sandbox | http://localhost:3000/match (not in primary nav) |
| Backend docs | http://localhost:8000/docs |

## Launch

```bash
# Terminal 1 — backend
cd backend
source .venv/bin/activate
python -m scripts.import_pudding_shades \
  --input app/data/external/pudding/allShades.csv \
  --output app/data/staging/pudding_all_shades.json
uvicorn app.main:app --reload --port 8000

# Terminal 2 — frontend
cd frontend
npm run dev
```

Open **http://localhost:3000/find-your-shade** — no OpenAI key required for this journey.

## Demo script

1. Homepage → **Find My Shade**.
2. Search `Punjab` or `NARS` → pick the **verified** Light Reflecting result when shown.
3. Choose depth correct + too warm → **Get my guidance**.
4. See explanation, next steps, candidate shades (when rules allow), and limitations.
5. Search a Maybelline / Fenty archive shade → guidance without invented candidates.
6. Optional: footer **Shade archive** for browse-only discovery.

## What works without AI

- Foundation search (historical + verified)
- Structured depth/undertone/wear guidance
- Verified candidate shades via `/api/match-shades`

## What still needs AI or richer data

- Natural-language “shade story” analysis via OpenAI (`/api/analyze-shade`)
- Broader verified catalog beyond the current NARS set
