"""Liveness payload for GET /health. ADK's own /health is stripped so this wins."""

from __future__ import annotations

import os
from typing import Any

from pipeline.adk_runtime import adk_available, engine_default, mcp_reachable, mcp_url
from pipeline.erp_provider import erp_live_configured, erp_status
from pipeline.extract import vertex_ready
from pipeline.factors_provider import factor_status
from pipeline.store import store_status


def health_payload() -> dict[str, Any]:
    store = store_status()
    factors = factor_status()
    erp = erp_status()
    mcp_ok = mcp_reachable()
    ready = bool(store.get("ok"))
    return {
        "ok": True,
        "ready": ready,
        "service": "greenchain-audit-lead",
        "model": os.environ.get("GEMINI_MODEL") or "gemini-3.5-flash",
        "store": store,
        "factors": factors,
        "erp": erp,
        "vertex": os.environ.get("GOOGLE_GENAI_USE_VERTEXAI"),
        "engine_default": engine_default(),
        "adk": adk_available(),
        "mcp": {"url": mcp_url(), "ok": mcp_ok},
        "vertex_ready": vertex_ready(),
        "erp_live": erp_live_configured(),
    }
