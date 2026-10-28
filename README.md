# ShadeWise 0.1 — The Foundation Fixer

ShadeWise helps people understand **why** a foundation shade does not match and **what to investigate next**.

Phase 1 is a polished local full-stack app with a real LLM integration for shade mismatch analysis — without inventing cross-brand shade equivalences or fake confidence scores.

## Stack

| Layer | Tech |
|-------|------|
| Frontend | Next.js App Router, TypeScript, Tailwind CSS |
| Backend | Python, FastAPI, Pydantic |
| AI | OpenAI API with structured outputs |
| Tests | Pytest (mocked LLM) |

PostgreSQL is intentionally deferred to a later phase.

## Project structure

```
Shadewise/
├── frontend/          # Next.js UI
├── backend/           # FastAPI + OpenAI
│   ├── app/
│   │   ├── api/       # HTTP routes
│   │   ├── models/    # Pydantic schemas
│   │   ├── prompts/   # Versioned LLM prompts
│   │   ├── services/  # Analysis orchestration
│   │   └── data/      # Illustrative catalog + guidance
│   ├── evals/         # Small mismatch evaluation set
│   └── tests/
├── docs/MANUAL_E2E.md
└── README.md
```

## Quick start

### 1. Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env and set OPENAI_API_KEY=sk-...
uvicorn app.main:app --reload --port 8000
```

API docs: [http://localhost:8000/docs](http://localhost:8000/docs)  
Health: [http://localhost:8000/health](http://localhost:8000/health)

### 2. Frontend

```bash
cd frontend
cp .env.example .env.local         # optional; defaults to http://localhost:8000
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

### 3. Tests

```bash
cd backend
source .venv/bin/activate
pytest -q
```

```bash
cd frontend
npm run lint
npm run build
```

## What Phase 1 does (and does not)

**Does**

- Collect a structured mismatch report from the user
- Call OpenAI from the **backend only** (API key never in the browser)
- Return structured analysis: summary, explanations, next steps, uncertainties
- Attach deterministic general guidance + explicitly illustrative catalog demos

**Does not**

- Detect undertone from photos
- Invent shade equivalences between brands
- Claim verified product recommendations without grounded data
- Include auth, payments, agents, RAG, or vector DBs

## Manual E2E

See [docs/MANUAL_E2E.md](docs/MANUAL_E2E.md).

## Eval set

See [backend/evals/shade_mismatch_cases.json](backend/evals/shade_mismatch_cases.json) and log live results in [backend/evals/RESULTS.md](backend/evals/RESULTS.md).

## Learning map — files to read first

1. `backend/app/models/schemas.py` — request/response contracts
2. `backend/app/prompts/shade_analysis.py` — what we ask the LLM
3. `backend/app/services/shade_analyzer.py` — LLM call + guidance merge
4. `backend/app/api/routes.py` — HTTP surface
5. `frontend/src/lib/api.ts` — how the UI talks to the API
6. `frontend/src/components/ShadeForm.tsx` — form → analyze → results

## Phase 2 ideas (not built yet)

- PostgreSQL for saved analyses and a verified product catalog
- Richer brand/product shade graphs with provenance
- Account history (optional light auth)
- Better eval harness with scored live runs
- Oxidation / wear-change specific flows with timed checklists
