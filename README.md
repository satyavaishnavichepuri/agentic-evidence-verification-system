# P14 - The Answer Contract with a Verified Path 

Our Project is an agentic research verification tool. You ask a question;
a pipeline of agents plans it, retrieves evidence, verifies claims, detects
contradictions, and returns a **validated Answer Contract** -- never an
unsupported, over-confident answer.

```
Question → Plan → RAG/Web Research → Evidence → Claim Verification
→ Answer Contract → VERIFIED / PARTIAL / DECLINED
```

Runs fully in **demo mode with zero API keys and zero database setup**.
Gemini and PostgreSQL are optional enhancements on top of the exact same
code paths, not separate modes.

## The Answer Contract

Every investigation produces one `AnswerContract`:

- Every finding (**claim**) must cite grounding **evidence**, or it is
  explicitly marked `unsupported` -- never silently presented as fact.
- Conflicting evidence produces a `contradicted` claim; the overall
  contract status becomes `PARTIAL` or `DECLINED`, never `VERIFIED`.
- Scope, citations, missing evidence, and contradictions are always shown.
- The contract is validated by **Pydantic models and plain Python business
  rules** (`backend/app/agents/contract_validator.py`), never by asking the
  LLM to grade its own answer. A validation failure downgrades the contract
  to `DECLINED` with the errors attached -- it never crashes the app.

## Agents

| Agent | Role |
|---|---|
| Planner | Decomposes the question into 3-5 subquestions |
| Research / RAG | Retrieves candidate evidence chunks via local TF-IDF search |
| Evidence | Synthesizes a claim per subquestion, strictly grounded in retrieved text |
| Verification | Classifies evidence stance (supports/contradicts/neutral) and derives claim status |
| Contradiction | Surfaces intra-claim and cross-claim evidence conflicts |
| Contract Validator | Assembles + validates the Answer Contract; derives overall status in code |

## Stack

- **Frontend:** React + TypeScript + Vite + Tailwind CSS
- **Backend:** FastAPI + Python, Pydantic v2
- **LLM:** Gemini API (optional; configured via `.env`)
- **RAG:** Local TF-IDF chunk retrieval (scikit-learn), PDF/TXT upload
- **Storage:** In-memory by default; PostgreSQL optional (JSON-blob persistence)

## Pages

- **Dashboard** -- all investigations and their contract outcomes
- **New Investigation** -- ask a question
- **Investigation Workspace** -- the main screen: question + subquestions +
  live agent progress (left), answer + findings + Answer Contract (center),
  sources + evidence + contradictions + evidence graph (right)
- **Evidence Explorer** -- every claim and its evidence, across all investigations
- **Knowledge Base** -- the RAG corpus; upload PDF/TXT/MD documents
- **Agent Monitor** -- live log of every agent execution system-wide

## Quick start

See **[runinstructions.md](runinstructions.md)** for full setup. Short version:

```bash
# backend
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env      # optional -- works with all fields blank
uvicorn app.main:app --reload

# frontend (new terminal)
cd frontend
npm install
cp .env.example .env
npm run dev
```

Open http://localhost:5173 -- a seeded demo knowledge base and two demo
investigations (one `PARTIAL`, one `DECLINED`) are loaded automatically, so
the whole workflow is visible immediately with no configuration.

## Enhancing with Gemini / PostgreSQL

Both are strictly additive:

- Set `GEMINI_API_KEY` in `backend/.env` to let the Planner, Evidence, and
  Verification agents use Gemini for sharper subquestion decomposition,
  claim synthesis, and evidence-stance classification. Every one of those
  calls has a deterministic fallback, so nothing breaks if the call fails.
- Set `DATABASE_URL` in `backend/.env` to persist investigations and the
  knowledge base in PostgreSQL instead of losing them on restart. If the
  connection fails, The system logs a warning and falls back to in-memory
  storage automatically -- it never hard-crashes on a bad `DATABASE_URL`.

See **[architecture.md](architecture.md)** for how the pipeline, contract
validation, and RAG index actually work, and for documented extension
points (e.g. wiring a real web-search API into the Research agent).
