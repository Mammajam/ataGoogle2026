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

Reproducible checks: [Testing](#testing).

Optional factor API (otherwise the offline catalog in `fixtures/factors.json` is used for kgCO₂e only — never for inventory quantities). Default is off.

```
GREENCHAIN_FACTOR_URL=https://example.com/factors
GREENCHAIN_FACTOR_TOKEN=
```

Adapter: `POST` JSON `{ "activity", "unit", "region", "year", "method", "scope", "category" }`. Success body must include `kgco2e_per_unit` (and optionally `id`, `source`, `method`). On timeout, HTTP error, or `error` in the body, GreenChain falls back to the offline catalog and logs `factor_source`.

## Testing

No pytest. GCP is not required for the deterministic suite. Activate the agent venv first (`agent/.venv`). Sample packs in `fixtures/samples/` are test fixtures only — they are never loaded as a default company.

### 1. Offline pipeline

From `agent/` (no servers):

```powershell
cd agent
python tests\test_pipeline.py
python tests\test_adk.py
```

```bash
cd agent
python tests/test_pipeline.py
python tests/test_adk.py
```

`test_pipeline.py` must print these lines (Starlette/ADK warnings are OK):

```
ok: northwind csv
ok: gate + memory
ok: harbor pack
ok: erp missing csv
ok: http 400
ok: health payload
ok: climatiq live mock
ok: live erp
ok: primitives
ok: extract unavailable
ok: extract vertex mock
ok: extract unavailable on error
ok: factor catalog
```

What that proves:

- Northwind CSV drafts diesel from **this run’s bytes**; electricity is not filled from `expected_draft` when vision is down.
- Dual kWh/MWh readings emit `ExtractionConfirm`; confirm to kWh yields ~38.142 tCO₂e; a second run for the same company applies policy with no widget.
- Harbor CSV (`activity.csv` aliases) drafts `diesel`, `electricity`, `road_freight` only — not Northwind lines.
- Empty upload is HTTP 400. `/health` is GreenChain-owned (`service: greenchain-audit-lead`).
- Factor catalog never invents inventory rows. Live Climatiq/ERP paths are mocked.

`test_adk.py` must print:

```
ok: engine default
skip: Vertex not configured
ok: adk skip/live probe
ok: mcp down forces deterministic
ok: mcp toolset preferred
```

If Vertex credentials are present, the skip line is omitted and the live probe still exits 0.

### 2. HTTP smoke (agent on :8080)

Start the agent as in Local spin-up. MCP is optional; without it the engine is `deterministic`. Then:

```powershell
cd agent
python tests\verify_http.py
```

```bash
cd agent
python tests/verify_http.py
```

This POSTs `fixtures/samples/harbor-logistics/erp_export.csv` as `activity.csv` for company `harbor-logistics`. Pass looks like:

```
health file … engine_default deterministic factors fixture erp_live False
run1 <uuid> company Harbor Logistics lines {'diesel', 'electricity', 'road_freight'}
OK
```

`engine_default` may be `adk` when Vertex + MCP are healthy. Fail if `company_id` is omitted, the CSV is missing, or diesel/electricity are absent.

### 3. Workspace close (browser)

With agent + web running ([http://localhost:3000](http://localhost:3000)):

| Step | Company id | Name | Year / region | Files |
| --- | --- | --- | --- | --- |
| A | `harbor-logistics` | Harbor Logistics | 2025 / UK | `fixtures/samples/harbor-logistics/erp_export.csv` |
| B | `northwind-energy` | Northwind Energy Ltd | 2025 / UK | all three files under `fixtures/samples/northwind/` |
| C | same as B | same | same | same pack again |

1. **A — Harbor CSV.** Run audit. Inventory keys are diesel, electricity, road freight (Scope 3 / C4). No A2UI widget. Collaboration stays “No material gap.”
2. **B — Northwind mixed pack.** Run audit. Diesel comes from the CSV. Without Vertex, electricity may be incomplete (`missing_quantity`) — never copied from another company. With Vertex, a kWh vs MWh conflict should open ExtractionConfirm when the tCO₂e delta is > 5% of company total. Confirm a unit; the widget clears and the line recalculates.
3. **C — Second close.** Same company id, same pack, Run audit. “Policy applied” chip; no ExtractionConfirm for that activity.

Do **not** expect a draft if company id is blank or no files are dropped (unless live ERP is configured).

Health while the agent is up: `GET http://localhost:8080/health` → `ok: true`, `service: greenchain-audit-lead`.

## Vercel (web workspace)

The Next.js app lives in `web/`, not the repo root. In the Vercel project: **Settings → General → Root Directory** must be `web`. Connecting GitHub without that setting makes the build look at the repo root, miss `next` in `package.json`, and fail with “No Next.js version detected.”

The production project `greenchain` is linked to `Mammajam/ataGoogle2026` on `main`. Set `AGENT_URL` (and CORS on the agent) in Vercel env vars.

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
