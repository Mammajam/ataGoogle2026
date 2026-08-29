"""Primitive inventory tools. Never invoke the full close — host/ADK orchestrate."""

from __future__ import annotations

import json

from pipeline.audit import confirm_extraction, persist_draft_lines, persist_line
from pipeline.store import get_store


def persist_line_tool(run_id: str, line_json: str) -> str:
    """Merge one inventory line into the draft. No extract, no A2UI."""
    raw = (line_json or "").strip()
    if not raw:
        return json.dumps({"error": "empty_line_json", "run_id": run_id})
    try:
        line = json.loads(raw)
    except json.JSONDecodeError as exc:
        return json.dumps({"error": "invalid_line_json", "detail": str(exc), "run_id": run_id})
    if not isinstance(line, dict):
        return json.dumps({"error": "line_not_object", "run_id": run_id})
    draft = persist_line(run_id, line)
    return json.dumps(
        {
            "run_id": draft["run_id"],
            "line_count": len(draft.get("lines") or []),
            "totals": draft.get("totals"),
        }
    )


def persist_draft_tool(run_id: str, company_id: str, lines_json: str = "[]") -> str:
    """Save the current line set and totals only. Host attaches A2UI later."""
    raw_lines = (lines_json or "").strip() or "[]"
    try:
        lines = json.loads(raw_lines)
    except json.JSONDecodeError as exc:
        return json.dumps({"error": "invalid_lines_json", "detail": str(exc), "run_id": run_id})
    if not isinstance(lines, list):
        return json.dumps({"error": "lines_not_array", "run_id": run_id})
    draft = persist_draft_lines(run_id, company_id, lines)
    return json.dumps(
        {
            "run_id": draft["run_id"],
            "status": draft.get("status"),
            "line_count": len(draft.get("lines") or []),
            "totals": draft.get("totals"),
        }
    )


def get_draft(run_id: str) -> str:
    """Read a previously persisted draft inventory."""
    draft = get_store().read_draft(run_id)
    if not draft:
        return json.dumps({"error": "not_found", "run_id": run_id})
    return json.dumps(draft)


def apply_extraction_confirm(
    run_id: str,
    line_id: str,
    quantity: float,
    unit: str,
    company_id: str,
) -> str:
    """Persist a widget answer as company policy and recompute that line only."""
    updated = confirm_extraction(
        run_id=run_id,
        line_id=line_id,
        quantity=quantity,
        unit=unit,
        company_id=company_id,
    )
    return json.dumps(
        {
            "run_id": updated["run_id"],
            "status": updated["status"],
            "totals": updated["totals"],
            "policy_keys": updated.get("policy_keys"),
        }
    )
