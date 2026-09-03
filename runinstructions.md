# Run Instructions

VeriScope AI works with **zero API keys and zero database setup**. Every
step below marked *(optional)* is a pure enhancement -- skip it and the app
still runs the full agentic pipeline against the seeded demo corpus.

## Prerequisites

- Python 3.10+
- Node.js 18+ and npm
- (optional) A Gemini API key from https://aistudio.google.com/apikey
- (optional) A running PostgreSQL instance

## 1. Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Copy the env template (all fields may stay blank for demo mode):

```bash
cp .env.example .env
```

*(optional)* Open `.env` and set:
```
GEMINI_API_KEY=your-key-here
DATABASE_URL=postgresql+psycopg2://user:pass@localhost:5432/veriscope
```

Start the API:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

On startup you'll see log lines confirming the active mode, e.g.:

```
[veriscope] Using in-memory storage (demo mode).
[veriscope] Seed knowledge base + demo investigations loaded.
```

or, with both optional features configured:

```
[veriscope] Postgres storage enabled.
[veriscope] Gemini enabled (gemini-1.5-flash).
```

Verify it's up: open http://localhost:8000/api/health -- you should see
`{"status": "ok", "gemini_enabled": false, "postgres_enabled": false}`
(or `true`/`true` if you configured the optional pieces).
Interactive API docs are at http://localhost:8000/docs.

## 2. Frontend

In a **new terminal**:

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

`frontend/.env` only needs `VITE_API_URL` -- it defaults to
`http://localhost:8000`, so you can usually leave it as-is.

Open **http://localhost:5173**.

## 3. What you should see immediately

- The **Dashboard** lists two seeded demo investigations: one about
  intermittent fasting (contract status `PARTIAL`, with one `verified`,
  one `contradicted`, one `partial`, and one `unsupported` claim) and one
  about a fictitious experimental compound (contract status `DECLINED`,
  because the corpus genuinely has no relevant evidence).
- Click into either one to see the full **Investigation Workspace**:
  question/subquestions/agent trace on the left, the answer and Answer
  Contract in the center, sources/evidence/contradictions/evidence graph
  on the right.
- The **Knowledge Base** page shows the 6 seeded sources. Try uploading a
  PDF or TXT file -- it's chunked and indexed immediately.
- Click **New Investigation**, ask a question related to the uploaded
  document or the seeded fasting/cardiovascular corpus, and watch the
  agent pipeline run live in the Workspace.
- The **Agent Monitor** shows every agent execution across the whole
  system, updating live.

## Troubleshooting

**Frontend can't reach the API / network errors in the browser console**
Confirm the backend is running on port 8000 and `frontend/.env`'s
`VITE_API_URL` matches. CORS is controlled by `CORS_ORIGINS` in
`backend/.env` -- it defaults to allowing `http://localhost:5173`.

**`pip install` fails on `psycopg2-binary`**
This only matters if you intend to use PostgreSQL. If you don't need it,
remove the `psycopg2-binary` and `SQLAlchemy` lines from
`backend/requirements.txt` before installing -- the app runs fine without
them as long as `DATABASE_URL` is left blank.

**Gemini calls seem to silently do nothing**
Check the backend startup logs for `[veriscope] Gemini configured but
failed to initialize: ...` or `Gemini call failed, using fallback
heuristic: ...`. VeriScope is designed to never crash on a bad Gemini
key/quota/network error -- it logs the failure and falls back to the
deterministic heuristic for that step, so the investigation still
completes.

**Postgres connection fails**
Check for `[veriscope] Postgres unavailable (...); falling back to
in-memory store.` in the backend logs. Fix the connection string / ensure
the database is reachable, then restart the backend.

**Uploaded PDF produces no evidence**
Some PDFs (scanned images without OCR text layer) have no extractable
text; `pypdf` will return an empty string and the upload is rejected with
a clear error. Use a text-based PDF or a `.txt`/`.md` file instead.

**I want to reset the demo data**
In-memory mode: just restart the backend process. Postgres mode: run
`TRUNCATE veriscope_kv;` against your database, then restart the backend
so it reseeds.
