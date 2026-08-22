"""GreenChain Audit Lead HTTP service.

Mounts the deterministic audit API always, and the ADK FastAPI app when google-adk
and Vertex credentials are present. Local file-store mode does not require GCP.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

AGENT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(AGENT_DIR))
load_dotenv(AGENT_DIR / ".env")

os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "TRUE")
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "us-central1")
os.environ.setdefault("GEMINI_MODEL", "gemini-3.5-flash")
os.environ.setdefault("GREENCHAIN_STORE", "file")

from pipeline.audit import confirm_extraction, run_audit  # noqa: E402
from pipeline.store import get_store  # noqa: E402

WEB_ORIGIN = os.environ.get("WEB_ORIGIN", "http://localhost:3000")
ALLOW_ORIGINS = [origin.strip() for origin in WEB_ORIGIN.split(",") if origin.strip()]
if "http://localhost:3000" not in ALLOW_ORIGINS:
    ALLOW_ORIGINS.append("http://localhost:3000")


class ConfirmBody(BaseModel):
    run_id: str
    line_id: str = "s2-grid-electricity"
    quantity: float = 184200
    unit: str = "kWh"
    company_id: str = "northwind-energy"


def _attach_routes(app: FastAPI) -> FastAPI:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOW_ORIGINS + ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/")
    def root() -> dict:
        return {
            "service": "greenchain-audit-lead",
            "health": "/health",
            "run": "POST /api/audit/run",
        }

    @app.get("/health")
    def health() -> dict:
        store_name = type(get_store()).__name__
        return {
            "ok": True,
            "service": "greenchain-audit-lead",
            "model": os.environ.get("GEMINI_MODEL", "gemini-3.5-flash"),
            "store": store_name,
            "vertex": os.environ.get("GOOGLE_GENAI_USE_VERTEXAI"),
        }

    @app.post("/api/audit/run")
    async def api_run_audit(
        company_id: str = Form(default="northwind-energy"),
        files: list[UploadFile] | None = File(default=None),
    ) -> dict:
        names = [item.filename or "upload" for item in files or []]
        draft = run_audit(company_id=company_id, filenames=names or None)
        return draft

    @app.post("/api/audit/confirm")
    def api_confirm(payload: ConfirmBody) -> dict:
        return confirm_extraction(
            run_id=payload.run_id,
            line_id=payload.line_id,
            quantity=payload.quantity,
            unit=payload.unit,
            company_id=payload.company_id,
        )

    @app.get("/api/audit/{run_id}")
    def api_get_draft(run_id: str) -> dict:
        draft = get_store().read_draft(run_id)
        if not draft:
            return {"error": "not_found", "run_id": run_id}
        return draft

    @app.get("/api/memory/{company_id}")
    def api_memory(company_id: str) -> dict:
        overrides = get_store().list_overrides(company_id)
        return {
            "company_id": company_id,
            "overrides": overrides,
            "policy_applied": bool(overrides),
        }

    return app


def build_app() -> FastAPI:
    try:
        from google.adk.cli.fast_api import get_fast_api_app

        session_uri = os.environ.get("SESSION_SERVICE_URI")
        kwargs = {
            "agents_dir": str(AGENT_DIR),
            "web": os.environ.get("ADK_WEB", "false").lower() == "true",
            "allow_origins": ALLOW_ORIGINS,
        }
        if session_uri:
            kwargs["session_service_uri"] = session_uri
        app = get_fast_api_app(**kwargs)
        app.title = "GreenChain Audit Lead"
        return _attach_routes(app)
    except Exception as exc:  # noqa: BLE001
        print(f"[greenchain] ADK FastAPI not mounted ({exc}); demo API is live.")
        app = FastAPI(title="GreenChain Audit Lead (file mode)")
        return _attach_routes(app)


app = build_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "8080")),
        reload=False,
    )
