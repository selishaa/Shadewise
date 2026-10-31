# ShadeWise Phase 1 — Eval Results

Prompt version: `shade_analysis_v1`  
Last reviewed: harness ready; live model pass not yet recorded in this environment.

## How to score a case

For each case in `shade_mismatch_cases.json`:

1. Ensure `OPENAI_API_KEY` is set in `backend/.env` and the API is running (`uvicorn app.main:app --reload --port 8000`).
2. From `backend/`, run:

   ```bash
   python -m scripts.run_shade_analysis_evals
   ```

3. Check the structured response against `expected` (script prints OK / FAIL / SOFT notes).
4. Mark **pass** only if all must_* rules hold and the soft should_* cues are clearly present.
5. Record notes — especially any invented shade equivalences (automatic fail).

## Results log

| Case ID | Status | Date | Notes |
|---------|--------|------|-------|
| depth_ok_too_orange | not_run | — | Run `python -m scripts.run_shade_analysis_evals` with a real key |
| depth_ok_too_pink | not_run | — | Run `python -m scripts.run_shade_analysis_evals` with a real key |
| too_dark_undertone_ok | not_run | — | Run `python -m scripts.run_shade_analysis_evals` with a real key |
| oxidizes_after_wear | not_run | — | Run `python -m scripts.run_shade_analysis_evals` with a real key |
| unclear_contradictory | not_run | — | Run `python -m scripts.run_shade_analysis_evals` with a real key |

Automated pytest coverage (mocked LLM + schema validation + rate limits) lives under `backend/tests/` and does **not** replace this live eval log.

## Local recording checklist

After a live run, replace `not_run` with `pass` or `fail`, add today’s date, and note:

- Any invented SKUs or cross-brand equivalences (fail)
- Missing uncertainties (fail)
- Confidence percentages or photo claims (fail)
- Soft undertone/depth cues that were weak but acceptable (note in Notes)
