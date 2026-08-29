# GreenChain

Collaborative Partner for GHG close. An analyst names a company and drops mixed evidence (ERP CSV, PDF bill, invoice photo). One ADK orchestrator (`audit_lead`, Gemini 3.5 Flash) drafts an inventory from **this run’s files**, then streams an A2UI widget only when two readings would move company tCO₂e by more than 5%. Confirming a unit is stored as company policy; the next run for that company applies it silently.

Track: **The Collaborative Partner** · All Things Agentic Hackathon

GreenChain is the product. The client is whoever you enter in the workspace — there is no runtime demo pack and no default company.

## Evidence format contract

A close requires a **company id**. Evidence is either uploaded files, a live ERP pull (`GREENCHAIN_ERP_URL`), or both.

Accepted upload types:

- **Tabular ERP:** UTF-8 `.csv`. After alias mapping, each row needs period, GHG scope, activity name, and either quantity+unit or spend.
- **Utility / invoice PDFs:** `.pdf`
- **Receipt / invoice photos:** `.jpg` `.jpeg` `.png` `.webp`

CSV column aliases (any one per field):

- period: `period_month`, `period`, `month`, `date`
- scope: `ghg_scope`, `scope`
- category: `ghg_category`, `category`
- activity: `activity_name`, `activity`
- quantity: `quantity`, `qty`, `volume`
- unit: `unit`, `uom`
- spend: `spend_gbp`, `spend`, `amount`, `value`
- optional: `site_id`, `site_name`, `vendor`, `notes`

A pack may be CSV-only, PDF/photo-only, or mixed. Missing a class yields an **incomplete** draft — lines are never filled from a sample company.

Example packs for tests and docs only (upload them like any client):

- `fixtures/samples/northwind/` — mixed energy close
- `fixtures/samples/harbor-logistics/` — logistics CSV using aliased headers

## Local spin-up (Windows PowerShell)

Needs Python 3.11+, Node 20+, and **pnpm**. GCP is **not** required for the deterministic close (file-store fallback).

```powershell
corepack enable
corepack prepare pnpm@10.14.0 --activate
```

**Terminal 1 — FastMCP** (required for the ADK engine)

```powershell
cd mcp
pip install -r requirements.txt
$env:PYTHONPATH = (Resolve-Path ..\agent).Path
python server.py
```

Set `MCP_URL=http://127.0.0.1:8081` in `agent/.env`. Start this **before** the agent when you want ADK. If MCP is down, the agent fails the ADK path loudly and falls back to deterministic instead of hanging.

**Terminal 2 — agent**

```powershell
cd agent
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python -m uvicorn main:app --reload --port 8080
```

**Terminal 3 — web**

```powershell
cd web
copy .env.example .env.local
pnpm install
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000). Enter company id / name / year / region, drop a conforming pack, **Run audit**.

Health: [http://localhost:8080/health](http://localhost:8080/health)

Pipeline checks (no pytest required):

```powershell
cd agent
python tests\test_pipeline.py
```

Optional factor API (otherwise the offline catalog in `fixtures/factors.json` is used for kgCO₂e only — never for inventory quantities). Default is off.

```
GREENCHAIN_FACTOR_URL=https://example.com/factors
GREENCHAIN_FACTOR_TOKEN=
```

Adapter: `POST` JSON `{ "activity", "unit", "region", "year", "method", "scope", "category" }`. Success body must include `kgco2e_per_unit` (and optionally `id`, `source`, `method`). On timeout, HTTP error, or `error` in the body, GreenChain falls back to the offline catalog and logs `factor_source`.

## Cloud Run

Requires the Google Cloud SDK (`gcloud`) on PATH.

```powershell
$env:GOOGLE_CLOUD_PROJECT = "your-gcp-project"
.\deploy\enable-apis.ps1
.\deploy\deploy-all.ps1
```

Three services: `greenchain-mcp`, `greenchain-agent` (with `MCP_URL`), then `greenchain-web`. CORS is the web origin. Model ID is `GEMINI_MODEL` (default `gemini-3.5-flash`). Secrets stay in Secret Manager — see `deploy/secrets.md`.

Set `GREENCHAIN_STORE=firestore` on the agent (the default when `GOOGLE_CLOUD_PROJECT` is a real id). Firestore holds drafts, company profiles, overrides, evidence, and ADK session ids. Run artifacts go to Firebase Storage / GCS (`GREENCHAIN_ARTIFACT_BUCKET`, default `{project}.appspot.com`). Local runs fall back to `agent/data/` if Firestore is unreachable. Client access is denied in `firestore.rules` / `storage.rules` — there is no login; only the agent SDK writes.

Live emission factors: set `CLIMATIQ_API_KEY`. Climatiq is queried per activity; `fixtures/factors.json` is offline fallback only and is never a source of inventory quantities.

Live ERP: set `GREENCHAIN_ERP_URL` (optional `GREENCHAIN_ERP_TOKEN`). `GET` with `company_id`, `year`, `region`, `run_id` must return `{ "rows": [ { "activity", "scope", "quantity", "unit", ... } ] }`. Uploaded CSV overlays the same activity keys; live ERP fills the rest. Files stay optional when ERP is configured.

Health: `GET http://localhost:8080/health` returns GreenChain diagnostics (`ok`, `engine_default`, `store`, `factors`, `erp`, `mcp`, `vertex_ready`). ADK’s `{ "status": "ok" }` is not used.

## Product shape

- One orchestrator: `audit_lead`. No Memory LLM.
- Gemini 3.5 Flash via Vertex. FastMCP is a running HTTP service; ERP tools read **this run’s** uploaded CSV (`run_id`), not a bundled fixture.
- A2UI v0.9 basic catalog only, produced by Python after the agent turn.
- GHG Protocol Scope 1–3 (categories as evidenced). Partial inventories are valid.
- Single page: company profile, dropzone, Run audit, inventory table, A2UI surface, memory chip.

## Devpost paste

See [docs/devpost.md](docs/devpost.md).
