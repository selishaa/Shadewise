# Manual end-to-end test (Phase 1)

Do this once both servers are running.

## Prerequisites

1. Backend: `uvicorn` on `http://localhost:8000` with a real `OPENAI_API_KEY` in `backend/.env`
2. Frontend: `npm run dev` on `http://localhost:3000`
3. Confirm `GET http://localhost:8000/health` returns `"status": "ok"` and `"openai_configured": true`

## Happy path

1. Open `http://localhost:3000` — confirm **ShadeWise** branding and the headline *Your shade exists. Let's find it.*
2. Click **Find My Shade**.
3. Fill the form:
   - Brand: Demo Cosmetics
   - Product: Everyday Soft Matte Foundation
   - Shade: Light 2 Warm
   - Depth: Depth feels correct
   - Undertone: Too orange / golden
   - Description: Depth looks right on my jaw but turns orange by midday.
   - Wear change: Yes
4. Click **Analyze my shade**.
5. Expect a results panel with:
   - Summary of the reported mismatch
   - Possible explanations + next steps
   - An explicit **Analysis ≠ verified recommendation** note
   - General guidance (not invented SKU matches)
   - Illustrative catalog rows labeled `illustrative`

## Error path (missing API key)

1. Temporarily rename/remove `OPENAI_API_KEY` from `backend/.env` and restart uvicorn.
2. Submit the form again.
3. Expect a clear error that the API key is not configured (HTTP 503) — not a crash.

## CORS / connectivity

1. Stop the backend.
2. Submit the form.
3. Expect a friendly message that the backend could not be reached.
