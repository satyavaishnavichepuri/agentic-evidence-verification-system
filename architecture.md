# Architecture

## Overview

The system is split into an independent FastAPI backend and a Vite/React
frontend that talks to it over HTTP. All research/verification logic lives
in the backend; the frontend only renders state and polls for progress.

```
frontend (Vite/React/TS) --HTTP--> backend (FastAPI)
                                        |
                                        v
                              agent pipeline (orchestrator.py)
                                        |
                    +-------------------+-------------------+
                    v                   v                   v
               storage.py           rag.py            gemini_client.py
          (in-memory / Postgres)  (TF-IDF index)     (optional, safe-fail)
```

## Request flow: creating an investigation

1. `POST /api/investigations {question}` creates an `Investigation` record
   (status `planning`, empty trace) and schedules
   `agents/orchestrator.run_investigation` as a FastAPI `BackgroundTask`.
   The endpoint returns immediately with the new investigation's id.
2. The frontend Workspace page polls `GET /api/investigations/{id}` every
   ~1.2s and renders `agent_trace`, `subquestions`, `claims`, `evidence`,
   and `contract` as they're filled in -- this is what makes agent
   progress feel live without websockets.
3. The orchestrator runs each agent in sequence, appending an `AgentStep`
   to `agent_trace` (status `running` → `done`/`failed`) around each call,
   with a small fixed pacing delay (`STEP_DELAY_SECONDS`) so the UI has
   something meaningful to show even on a fast local corpus.

## The agent pipeline

### 1. Planner (`agents/planner.py`)
Turns the question into 3-5 subquestions. If `GEMINI_API_KEY` is set, asks
Gemini for a JSON array of subquestions; otherwise (or on any Gemini
failure) falls back to a fixed decomposition template that always includes
a subquestion probing for counter-evidence. **This fallback is what makes
demo mode work with zero keys** -- every agent below has the same shape.

### 2. Research / RAG (`agents/research.py`, `rag.py`)
For each subquestion, retrieves the top-K chunks from the corpus via
TF-IDF + cosine similarity (`sklearn`). The corpus is the union of:
- the seeded demo knowledge base (`seed.py`)
- anything uploaded through the Knowledge Base page (`routers/documents.py`)

**Note on "web research":** to keep the zero-API-key guarantee real, this
build does not call an external search API. Seed sources tagged
`type="web"` simulate previously-retrieved web research so the UI and
workflow (including a source-type breakdown) are fully exercised. Wiring
a real search API is a documented extension point below.

### 3. Evidence (`agents/evidence.py`)
For each subquestion, drafts one `Claim` whose text is synthesized *only*
from the retrieved chunks -- never invented. If Gemini is configured it
phrases a tighter one-sentence synthesis; otherwise a deterministic
heuristic uses the top-scoring chunk. Every retrieved chunk above a
relevance floor becomes an `EvidenceItem` attached to that claim.

### 4. Verification (`agents/verification.py`)
Two responsibilities, both documented in-code:
- **Stance classification**: for each evidence item without an authored
  stance (only the seed corpus has hand-authored `stance_hint`s), decide
  `supports` / `contradicts` / `neutral`. Uses Gemini if available;
  otherwise a transparent relevance-threshold heuristic (see
  `SUPPORT_RELEVANCE_FLOOR` / `STRONG_RELEVANCE` constants). This
  heuristic is intentionally conservative and is *not* a real NLI model --
  that's a known limitation, stated here rather than hidden.
- **Claim status derivation**: turns the stance-labeled evidence set into
  `verified` / `partial` / `contradicted` / `unsupported` using counts and
  thresholds in plain Python. The LLM, when used, is only ever asked about
  one snippet at a time ("does this support the claim?") -- never "is this
  claim true?".

### 5. Contradiction (`agents/contradiction.py`)
- **Intra-claim**: a claim with both supporting and contradicting evidence
  becomes a `Contradiction` record referencing that claim.
- **Cross-claim**: a lightweight lexical-overlap heuristic flags pairs of
  claims about closely related subject matter whose evidence stances point
  in opposite directions. This is a best-effort signal, not full NLI.

### 6. Contract Validator (`agents/contract_validator.py`)
This is the enforcement point for the whole system's core promise. Two
independent layers:
1. **Pydantic schema validation** (`models.AnswerContract`'s
   `@model_validator`s) -- e.g. every claim's `evidence_ids` must be
   non-empty unless its status is `unsupported`; every `Contradiction`
   must reference real claim ids.
2. **Business-rule status derivation**, in plain Python
   (`_derive_status`): the overall `VERIFIED` / `PARTIAL` / `DECLINED`
   status is computed from claim-status counts, never asserted by an LLM.

If either layer fails, the contract is **not discarded**. It's downgraded
to `DECLINED`, the concrete validation errors are attached
(`validation_errors`) and rendered in the Workspace UI, and the
investigation still completes normally. A validation failure is a
legitimate, visible outcome -- not a crash.

## Data model

All shapes are defined once, in `backend/app/models.py`, as Pydantic
models, and mirrored by hand in `frontend/src/types/index.ts`. Key types:
`Source`, `Chunk`, `SubQuestion`, `EvidenceItem`, `Claim`, `Contradiction`,
`AnswerContract`, `AgentStep`, `Investigation`.

## Storage

`backend/app/storage.py` defines a small `BaseStore` interface
(`save/get/list` for investigations, sources, chunks) with two
implementations:

- **`InMemoryStore`** (default) -- plain Python dicts. Zero setup, resets
  on restart.
- **`PostgresStore`** (opt-in via `DATABASE_URL`) -- persists the exact
  same Pydantic-model JSON in a single `The system_kv(key, kind, value
  JSONB)` table. This is intentionally a key-value upgrade, not a
  relational schema fork, so agent code never needs to know which backend
  is active. If the Postgres connection fails at startup, The system logs a
  warning and falls back to `InMemoryStore` rather than crashing.

## RAG index

`backend/app/rag.py` chunks text into ~480-character windows (with
overlap, breaking on sentence/word boundaries where possible) and indexes
all chunks with `TfidfVectorizer` + cosine similarity. The index is
rebuilt on any new upload (`rag_index.mark_dirty()`), which is O(n) but
fine at demo/small-corpus scale. No embeddings API, no vector DB --
this is what makes local RAG work with zero setup.

## Evidence graph

`backend/app/graph.py` builds a `Question -> Claim -> Evidence -> Source`
graph from a completed investigation (`GET
/api/investigations/{id}/graph`). The frontend renders it as a nested,
color-coded column diagram (`components/EvidenceGraphView.tsx`) rather
than a force-directed layout, trading visual flourish for something that
renders correctly with zero extra dependencies and is easy to read.

## Frontend structure

- `src/api/client.ts` -- typed Axios client, one function per endpoint
- `src/types/index.ts` -- TypeScript mirror of the backend Pydantic models
- `src/components/` -- `Layout` (sidebar nav), `StatusBadge` (contract/
  claim/stance badges), `EvidenceGraphView`
- `src/pages/` -- one file per page (Dashboard, NewInvestigation,
  Workspace, EvidenceExplorer, KnowledgeBase, AgentMonitor)

The Workspace page polls `GET /api/investigations/{id}` on an interval
while `status` is not yet `complete`/`failed`; this is the entire "live
agent progress" mechanism -- no websockets, no extra infrastructure.

## Known limitations (stated, not hidden)

- Stance classification without Gemini is a relevance-threshold heuristic,
  not a real entailment/NLI model. It is deliberately conservative.
- "Web research" in local/demo mode is simulated via seed sources tagged
  `web`; no external search API is called by default.
- The evidence graph and cross-claim contradiction detection use
  lightweight heuristics (lexical overlap), not deep semantic matching.
- The RAG index rebuilds from scratch on every upload; fine for a demo
  corpus, not tuned for large-scale ingestion.

## Extension points

- **Real web search**: add a `web_search.py` agent step that calls a
  search API, converts results into `Source`/`Chunk` records exactly like
  `routers/documents.py` does for uploads, and feeds them into the same
  `rag_index`. Everything downstream (evidence, verification, contract)
  already works generically over the corpus.
- **Real NLI stance model**: swap the heuristic in
  `verification._classify_stance`'s fallback branch for a call to a local
  or hosted entailment model; the Gemini branch already models the
  intended interface (`SUPPORTS` / `CONTRADICTS` / `NEUTRAL`).
- **Relational Postgres schema**: `PostgresStore` can be replaced with a
  proper SQLAlchemy ORM schema without touching any agent code, since all
  reads/writes go through `BaseStore`.
