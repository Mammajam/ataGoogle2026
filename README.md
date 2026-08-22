# GreenChain

Collaborative Partner for GHG close. An analyst drops mixed evidence (ERP CSV, PDF bill, invoice photo). One ADK orchestrator (`audit_lead`, Gemini 3.5 Flash) drafts a complete inventory via ERP + factor tools, then streams an A2UI widget **only** for the planted kWh/MWh conflict. Confirming that unit is stored as company policy; the next run applies it silently.

Track: **The Collaborative Partner** · All Things Agentic Hackathon

## Repo layout

```
ataGoogle2026/
  README.md
  docs/architecture.md
  docs/devpost.md
  fixtures/                  # deterministic demo pack
  agent/                     # Python ADK + FastAPI (Cloud Run)
  mcp/                       # FastMCP HTTP wrappers of the same tools
  web/                       # Next.js App Router (Cloud Run)
  deploy/                    # gcloud scripts (PowerShell + bash)
```

## Local spin-up (Windows PowerShell)

Needs Python 3.11+, Node 20+, and **pnpm** (this repo does not use npm or yarn). GCP is **not** required for the demo loop (file-store fallback).

```powershell
corepack enable
corepack prepare pnpm@10.14.0 --activate
```

**Terminal 1 — agent**

```powershell
cd agent
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python -m uvicorn main:app --reload --port 8080
```

**Terminal 2 — web**

```powershell
cd web
copy .env.example .env.local
pnpm install
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000). Click **Use demo pack** → **Run audit**. Do not type.

Health check: [http://localhost:8080/health](http://localhost:8080/health)

Optional MCP server (same tools over HTTP):

```powershell
cd mcp
pip install -r requirements.txt
$env:PYTHONPATH = (Resolve-Path ..\agent).Path
python server.py
```

Regenerate planted PDF/JPEG:

```powershell
python fixtures\generate.py
```

Pipeline checks (no pytest required):

```powershell
cd agent
python tests\test_pipeline.py
```

## Demo script (4 minutes, unedited — record this; no video is stored in the repo)

**0:00–0:35 — Problem.** Show `fixtures/erp_export.csv` (blank Scope 2/3 quantities), `electricity_bill.pdf` (184,200 kWh + MWh-equivalent trap), `diesel_receipt.jpg`. “Static tools stop. We will not chat first.”

**0:35–1:50 — Autonomy.** Click **Run audit**. Draft appears with Scope 1 diesel, Scope 2 electricity, Scope 3 Category 1 spend lines. Each row: source thumbnail, method, tCO₂e, confidence. Analyst has typed nothing.

**1:50–2:50 — Collaboration.** Red/material electricity line: kWh vs MWh. A2UI `ExtractionConfirm` (basic catalog: Card / Text / Button). Confirm **184,200 kWh**. Line and totals recalculate. “GreenChain will remember this for this company.”

**2:50–3:25 — Memory.** Run audit again on the same pack. **No widget.** Chip: **Policy applied**. Draft uses last period’s kWh.

**3:25–4:00 — Proof.** Cloud Run URL / Vertex logs if deployed. “GreenChain leads the close, takes notes, and only asks when the number would be wrong.” Stop.

## Cloud Run

Requires the Google Cloud SDK (`gcloud`) on PATH. This workspace did not have it installed, so live deploy was not executed.

```powershell
$env:GOOGLE_CLOUD_PROJECT = "your-gcp-project"
.\deploy\enable-apis.ps1
.\deploy\deploy-all.ps1
```

Two services: `greenchain-agent` then `greenchain-web`. CORS is the web origin. Model ID is `GEMINI_MODEL` (default `gemini-3.5-flash`). Secrets stay in Secret Manager — see `deploy/secrets.md`. No keys in this repo.

Set `GREENCHAIN_STORE=firestore` on the agent service once a Firestore database exists in `us-central1`. Local default is the JSON file store under `agent/data/`.

## What is locked

- One orchestrator: `audit_lead`. No Memory LLM.
- Gemini 3.5 Flash via Vertex (`GOOGLE_GENAI_USE_VERTEXAI=TRUE`). Model ID from env.
- FunctionTools over fixture JSON; FastMCP wraps the same functions in `mcp/`.
- A2UI v0.9 **basic catalog** only (Card, Column, Text, Button).
- Scope: `northwind-energy`, 12 months, Scope 1 fuel + Scope 2 electricity + Scope 3 Category 1.
- Single page: dropzone, Run audit, inventory table, A2UI surface, memory chip.

## Stretch skipped

- Voice note
- Custom A2UI catalog widgets
- Live GCP deploy (run the scripts when authenticated)
- Recording the 4-minute video (use the script above)

## Devpost paste

See [docs/devpost.md](docs/devpost.md).
