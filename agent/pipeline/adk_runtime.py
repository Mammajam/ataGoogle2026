"""ADK Runner: session + file parts + MCP tools. Falls back to run_audit()."""

from __future__ import annotations

import asyncio
import json
import os
import uuid
from collections.abc import AsyncIterator
from typing import Any

from pipeline.audit import (
    assemble_from_evidence,
    attach_material_gate,
    empty_draft,
    load_company,
    persist_draft_lines,
    run_audit,
)
from pipeline.classify import classify_uploads
from pipeline.erp_provider import erp_live_configured
from pipeline.extract import extract_artifacts, vertex_ready
from pipeline.store import get_store

APP_NAME = "greenchain"
ADK_TIMEOUT_SEC = 90.0


class CloseError(ValueError):
    """Invalid close request (missing company or files)."""


def mcp_url() -> str:
    return (os.environ.get("MCP_URL") or "http://127.0.0.1:8081").rstrip("/")


def mcp_reachable() -> bool:
    """True when FastMCP HTTP is up. 4xx still counts — / is 404 and /mcp is 406 without MCP headers."""
    import urllib.error
    import urllib.request

    url = mcp_url()
    for target in (url, url + "/mcp"):
        try:
            req = urllib.request.Request(target, method="GET")
            with urllib.request.urlopen(req, timeout=1.5) as res:
                return int(res.status) < 500
        except urllib.error.HTTPError as exc:
            if int(exc.code) < 500:
                return True
        except Exception:
            continue
    return False


def adk_available() -> bool:
    try:
        from audit_lead.agent import root_agent

        return root_agent is not None
    except Exception:
        return False


def engine_default() -> str:
    force = (os.environ.get("GREENCHAIN_FORCE_DETERMINISTIC") or "").lower()
    if force in {"1", "true", "yes"}:
        return "deterministic"
    if vertex_ready() and adk_available() and mcp_reachable():
        return "adk"
    return "deterministic"


def _event(step: str, message: str) -> dict[str, str]:
    return {"step": step, "message": message}


def _mime(name: str) -> str:
    lower = name.lower()
    if lower.endswith(".pdf"):
        return "application/pdf"
    if lower.endswith(".png"):
        return "image/png"
    if lower.endswith(".webp"):
        return "image/webp"
    if lower.endswith(".csv"):
        return "text/csv"
    return "image/jpeg"


def _save_uploads(run_id: str, uploads: list[dict[str, Any]]) -> list[str]:
    store = get_store()
    names = []
    for item in uploads:
        name = str(item.get("filename") or "upload.bin")
        data = item.get("bytes") or b""
        store.write_artifact(run_id, name, data)
        names.append(name)
    return names


def _map_adk_event(event: Any) -> dict[str, str] | None:
    calls = []
    if hasattr(event, "get_function_calls"):
        try:
            calls = list(event.get_function_calls() or [])
        except Exception:
            calls = []
    if not calls and getattr(event, "content", None) is not None:
        for part in getattr(event.content, "parts", None) or []:
            fc = getattr(part, "function_call", None)
            if fc is not None:
                calls.append(fc)
    if calls:
        names = ", ".join(getattr(c, "name", None) or str(c) for c in calls)
        return _event("tool_call", f"Gemini called {names}.")

    responses = []
    if hasattr(event, "get_function_responses"):
        try:
            responses = list(event.get_function_responses() or [])
        except Exception:
            responses = []
    if not responses and getattr(event, "content", None) is not None:
        for part in getattr(event.content, "parts", None) or []:
            fr = getattr(part, "function_response", None)
            if fr is not None:
                responses.append(fr)
    if responses:
        names = ", ".join(getattr(r, "name", None) or str(r) for r in responses)
        return _event("tool_result", f"Tool returned {names}.")

    is_final = False
    if callable(getattr(event, "is_final_response", None)):
        try:
            is_final = bool(event.is_final_response())
        except Exception:
            is_final = False
    if is_final or getattr(event, "partial", False):
        return _event("model", "Gemini 3.5 Flash generateContent.")
    return None


async def run_close(
    *,
    company_id: str,
    uploads: list[dict[str, Any]],
    company_name: str | None = None,
    reporting_year: int | None = None,
    region: str | None = None,
) -> AsyncIterator[dict[str, Any]]:
    """Yield job-log events; final event type=draft includes the inventory."""
    if not (company_id or "").strip():
        raise CloseError("company_id is required")
    real = [item for item in uploads if item.get("bytes")]
    if not real and not erp_live_configured():
        raise CloseError("At least one evidence file is required")

    run_id = str(uuid.uuid4())
    names = _save_uploads(run_id, real)
    classified = classify_uploads(real)
    company = load_company(
        company_id.strip(), name=company_name, reporting_year=reporting_year, region=region
    )
    yield _event("session", f"Opened close {run_id} for {company_id}.")

    extract = extract_artifacts(real)
    if extract.source != "vertex":
        yield _event("vision_unavailable", extract.reason or "Vision/Vertex unavailable.")
    else:
        yield _event("extract", f"Gemini vision extract confidence {extract.confidence:.0%}.")

    engine = engine_default()
    kwargs = dict(
        company_id=company_id.strip(),
        company_name=company.get("name"),
        reporting_year=company.get("reporting_year"),
        region=company.get("region"),
        filenames=names,
        extract=extract.as_dict(),
        run_id=run_id,
        classified=classified,
    )
    if engine != "adk":
        if not mcp_reachable() and vertex_ready() and adk_available():
            yield _event("fallback", "MCP is down — failing the ADK path instead of hanging.")
        else:
            yield _event("fallback", "ADK/Vertex/MCP not ready — deterministic close.")
        draft = run_audit(engine="deterministic", **kwargs)
        yield {"step": "draft", "message": "Draft ready.", "draft": draft, "type": "draft"}
        return

    yield _event("model", "Starting Audit Lead on Gemini 3.5 Flash.")
    try:
        draft = None
        async with asyncio.timeout(ADK_TIMEOUT_SEC):
            async for item in _run_adk(run_id, company, names, real, extract, classified):
                if item.get("type") == "draft":
                    draft = item["draft"]
                else:
                    yield item
        yield {"step": "draft", "message": "Draft ready.", "draft": draft, "type": "draft"}
    except TimeoutError:
        yield _event("fallback", "ADK timed out; deterministic close.")
        draft = run_audit(engine="deterministic", **kwargs)
        yield {"step": "draft", "message": "Draft ready.", "draft": draft, "type": "draft"}
    except Exception as exc:  # noqa: BLE001
        yield _event("fallback", f"ADK failed ({exc}); deterministic close.")
        draft = run_audit(engine="deterministic", **kwargs)
        yield {"step": "draft", "message": "Draft ready.", "draft": draft, "type": "draft"}


async def confirm_close(
    *,
    run_id: str,
    line_id: str,
    quantity: float,
    unit: str,
    company_id: str,
) -> AsyncIterator[dict[str, Any]]:
    from pipeline.audit import confirm_extraction

    session = get_store().load_session(run_id)
    if engine_default() == "adk" and session and adk_available() and mcp_reachable():
        yield _event("model", "Continuing Audit Lead session for ExtractionConfirm.")
        try:
            async with asyncio.timeout(ADK_TIMEOUT_SEC):
                async for item in _confirm_adk(run_id, company_id, line_id, quantity, unit, session):
                    yield item
        except Exception as exc:  # noqa: BLE001
            yield _event("fallback", f"ADK confirm failed ({exc}); applying Python confirm.")
    elif engine_default() == "adk" and not mcp_reachable():
        yield _event("fallback", "MCP is down — applying Python confirm instead of hanging.")
    draft = confirm_extraction(
        run_id=run_id,
        line_id=line_id,
        quantity=quantity,
        unit=unit,
        company_id=company_id,
    )
    yield {"step": "draft", "message": "Policy persisted.", "draft": draft, "type": "draft"}


async def _run_adk(
    run_id: str,
    company: dict[str, Any],
    names: list[str],
    uploads: list[dict[str, Any]],
    extract: Any,
    classified: list[dict[str, Any]],
) -> AsyncIterator[dict[str, Any]]:
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai import types

    from audit_lead.agent import root_agent

    company_id = str(company["company_id"])
    store = get_store()
    store.write_draft(run_id, empty_draft(run_id, company_id, names, company))
    session_service = InMemorySessionService()
    session = await session_service.create_session(
        app_name=APP_NAME, user_id=company_id, session_id=run_id
    )
    store.save_session(
        run_id, {"session_id": session.id, "user_id": company_id, "app_name": APP_NAME}
    )
    _ADK_SERVICES[run_id] = session_service

    runner = Runner(agent=root_agent, app_name=APP_NAME, session_service=session_service)
    prompt = (
        f"Run the GHG close for company_id={company_id} name={company.get('name')} "
        f"year={company.get('reporting_year')} region={company.get('region')}. "
        f"run_id={run_id}. Extract JSON: {json.dumps(extract.as_dict())}. "
        "Call memory_load with company_id, erp_get_activity with run_id and company_id, "
        "factors_lookup with this company's region and year, "
        "inventory_persist_line, inventory_persist_draft. Persist only activities present "
        "in the attached evidence. Do not emit A2UI."
    )
    parts: list[Any] = [types.Part.from_text(text=prompt)]
    for item in uploads:
        name = str(item.get("filename") or "")
        data = item.get("bytes") or b""
        if not data:
            continue
        if name.lower().endswith(".csv"):
            parts.append(types.Part.from_text(text=data.decode("utf-8", errors="replace")))
        else:
            parts.append(types.Part.from_bytes(data=data, mime_type=_mime(name)))

    async for event in runner.run_async(
        user_id=company_id,
        session_id=session.id,
        new_message=types.Content(role="user", parts=parts),
    ):
        mapped = _map_adk_event(event)
        if mapped:
            yield mapped

    draft = store.read_draft(run_id)
    lines = (draft or {}).get("lines") or []
    evidence_lines, override_map, erp = assemble_from_evidence(
        run_id=run_id, company=company, extract=extract.as_dict(), artifacts=names
    )
    if len(lines) < len(evidence_lines) or len(lines) == 0:
        draft = persist_draft_lines(
            run_id,
            company_id,
            evidence_lines,
            artifacts=names,
            events=[
                {"step": "model", "message": "Gemini 3.5 Flash completed the ADK turn."},
                {"step": "tools", "message": "Host assembled lines from this run's evidence."},
            ],
            engine="adk",
            company=company,
        )
        draft["erp_row_count"] = erp.get("row_count", 0)
        draft["policy_keys"] = list(override_map.keys())
        draft["classified"] = classified
    draft = attach_material_gate(draft or empty_draft(run_id, company_id, names, company))
    draft["engine"] = "adk"
    draft["model"] = os.environ.get("GEMINI_MODEL") or "gemini-3.5-flash"
    store.write_draft(run_id, draft)
    yield {"step": "draft", "message": "Draft ready.", "draft": draft, "type": "draft"}


async def _confirm_adk(
    run_id: str,
    company_id: str,
    line_id: str,
    quantity: float,
    unit: str,
    session_meta: dict[str, Any],
) -> AsyncIterator[dict[str, Any]]:
    from google.adk.runners import Runner
    from google.genai import types

    from audit_lead.agent import root_agent

    session_service = _ADK_SERVICES.get(run_id)
    if session_service is None:
        from google.adk.sessions import InMemorySessionService

        session_service = InMemorySessionService()
        await session_service.create_session(
            app_name=APP_NAME, user_id=company_id, session_id=run_id
        )
        _ADK_SERVICES[run_id] = session_service

    runner = Runner(agent=root_agent, app_name=APP_NAME, session_service=session_service)
    text = (
        f"Analyst confirmed run_id={run_id} line_id={line_id} "
        f"quantity={quantity} unit={unit} company_id={company_id}. Call inventory_confirm now."
    )
    async for event in runner.run_async(
        user_id=company_id,
        session_id=str(session_meta.get("session_id") or run_id),
        new_message=types.Content(role="user", parts=[types.Part.from_text(text=text)]),
    ):
        mapped = _map_adk_event(event)
        if mapped:
            yield mapped


_ADK_SERVICES: dict[str, Any] = {}
