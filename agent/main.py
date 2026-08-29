"""GreenChain Audit Lead HTTP service.

Deterministic /api/audit/run always works. When Vertex + ADK + MCP are healthy,
the same route drives an ADK session (Gemini sees PDF/JPEG) and can stream SSE.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response, StreamingResponse
from pydantic import BaseModel

AGENT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(AGENT_DIR))
load_dotenv(AGENT_DIR / ".env")

os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "TRUE")
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "us-central1")
os.environ.setdefault("GEMINI_MODEL", "gemini-3.5-flash")
os.environ.setdefault("GREENCHAIN_STORE", "file")
os.environ.setdefault("MCP_URL", "http://127.0.0.1:8081")

from pipeline.adk_runtime import (  # noqa: E402
    CloseError,
    confirm_close,
    run_close,
)
from pipeline.erp_provider import erp_live_configured  # noqa: E402
from pipeline.health import health_payload  # noqa: E402
from pipeline.store import get_store  # noqa: E402

WEB_ORIGIN = os.environ.get("WEB_ORIGIN", "http://localhost:3000")
ALLOW_ORIGINS = [origin.strip() for origin in WEB_ORIGIN.split(",") if origin.strip()]
if "http://localhost:3000" not in ALLOW_ORIGINS:
    ALLOW_ORIGINS.append("http://localhost:3000")


class ConfirmBody(BaseModel):
    run_id: str
    line_id: str
    quantity: float
    unit: str
    company_id: str


def _uploads(files: list[UploadFile] | None) -> list[dict[str, Any]]:
    items = []
    for item in files or []:
        data = item.file.read() if item.file else b""
        items.append(
            {
                "filename": item.filename or "upload.bin",
                "bytes": data,
                "content_type": item.content_type,
            }
        )
    return items


def _sse(payload: dict[str, Any]) -> str:
    event = payload.get("type") or payload.get("step") or "log"
    return f"event: {event}\ndata: {json.dumps(payload)}\n\n"


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
        return health_payload()

    @app.get("/ready")
    def ready() -> dict:
        payload = health_payload()
        if not payload.get("ready"):
            return JSONResponse(payload, status_code=503)
        return payload

    @app.post("/api/audit/run")
    async def api_run_audit(
        request: Request,
        company_id: str = Form(...),
        company_name: str = Form(default=""),
        reporting_year: str = Form(default=""),
        region: str = Form(default=""),
        files: list[UploadFile] | None = File(default=None),
    ):
        uploads = _uploads(files)
        cid = (company_id or "").strip()
        if not cid:
            raise HTTPException(status_code=400, detail="company_id is required")
        if (not uploads or not any(item.get("bytes") for item in uploads)) and not erp_live_configured():
            raise HTTPException(status_code=400, detail="at least one evidence file is required")
        year = None
        if (reporting_year or "").strip():
            try:
                year = int(reporting_year)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail="reporting_year must be an integer") from exc
        want_sse = "text/event-stream" in (request.headers.get("accept") or "")
        kwargs = {
            "company_id": cid,
            "uploads": uploads,
            "company_name": (company_name or "").strip() or None,
            "reporting_year": year,
            "region": (region or "").strip() or None,
        }

        if want_sse:

            async def gen():
                try:
                    async for event in run_close(**kwargs):
                        yield _sse(event)
                except CloseError as exc:
                    yield _sse({"step": "error", "message": str(exc)})

            return StreamingResponse(
                gen(),
                media_type="text/event-stream",
                headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
            )

        draft = None
        try:
            async for event in run_close(**kwargs):
                if event.get("type") == "draft":
                    draft = event["draft"]
        except CloseError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return JSONResponse(draft or {"error": "no_draft"})

    @app.post("/api/audit/confirm")
    async def api_confirm(payload: ConfirmBody) -> dict:
        draft = None
        async for event in confirm_close(
            run_id=payload.run_id,
            line_id=payload.line_id,
            quantity=payload.quantity,
            unit=payload.unit,
            company_id=payload.company_id,
        ):
            if event.get("type") == "draft":
                draft = event["draft"]
        return draft or {"error": "no_draft"}

    @app.get("/api/audit/{run_id}/artifacts/{filename}")
    def api_get_artifact(run_id: str, filename: str):
        from pathlib import Path

        name = Path(filename).name
        data = get_store().read_artifact(run_id, name)
        if data is None:
            raise HTTPException(status_code=404, detail="artifact not found")
        lower = name.lower()
        media = "application/octet-stream"
        if lower.endswith(".csv"):
            media = "text/csv"
        elif lower.endswith(".pdf"):
            media = "application/pdf"
        elif lower.endswith(".png"):
            media = "image/png"
        elif lower.endswith(".webp"):
            media = "image/webp"
        elif lower.endswith((".jpg", ".jpeg")):
            media = "image/jpeg"
        return Response(content=data, media_type=media)

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


def _drop_adk_health_routes(app: FastAPI) -> None:
    """ADK FastAPI registers GET /health first; keep GreenChain's payload instead."""
    kept = []
    for route in app.router.routes:
        path = getattr(route, "path", None)
        methods = getattr(route, "methods", None) or set()
        if path in {"/health", "/healthz"} and (not methods or "GET" in methods):
            continue
        kept.append(route)
    app.router.routes = kept


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
        _drop_adk_health_routes(app)
        return _attach_routes(app)
    except Exception as exc:  # noqa: BLE001
        print(f"[greenchain] ADK FastAPI not mounted ({exc}); file-mode API is live.")
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
