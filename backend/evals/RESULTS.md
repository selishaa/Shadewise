# ShadeWise Phase 1 — Eval Results

Prompt version: `shade_analysis_v1`  
Last reviewed: not yet run against a live model in this environment.

## How to score a case

For each case in `shade_mismatch_cases.json`:

1. POST the `input` to `/api/analyze-shade` (requires a configured `OPENAI_API_KEY`).
2. Check the structured response against `expected`.
3. Mark **pass** only if all must_* rules hold and the soft should_* cues are clearly present.
4. Record notes — especially any invented shade equivalences (automatic fail).

## Results log

| Case ID | Status | Date | Notes |
|---------|--------|------|-------|
| depth_ok_too_orange | not_run | — | Needs live API key to evaluate |
| depth_ok_too_pink | not_run | — | Needs live API key to evaluate |
| too_dark_undertone_ok | not_run | — | Needs live API key to evaluate |
| oxidizes_after_wear | not_run | — | Needs live API key to evaluate |
| unclear_contradictory | not_run | — | Needs live API key to evaluate |

Automated pytest coverage (mocked LLM + schema validation) lives under `backend/tests/` and does **not** replace this live eval log.
