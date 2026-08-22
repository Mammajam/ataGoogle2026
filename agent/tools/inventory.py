from __future__ import annotations

import json

from pipeline.audit import confirm_extraction, run_audit
from pipeline.store import get_store


def write_draft(company_id: str = "northwind-energy") -> str:
    """Run the close and persist a complete draft inventory. Never ask before writing."""
    draft = run_audit(company_id=company_id)
    return json.dumps(
        {
            "run_id": draft["run_id"],
            "status": draft["status"],
            "totals": draft["totals"],
            "line_count": len(draft["lines"]),
            "widget_kind": (draft.get("widget") or {}).get("kind"),
            "policy_applied": draft.get("policy_applied"),
        }
    )


def get_draft(run_id: str) -> str:
    """Read a previously written draft inventory."""
    draft = get_store().read_draft(run_id)
    if not draft:
        return json.dumps({"error": "not_found", "run_id": run_id})
    return json.dumps(draft)


def apply_extraction_confirm(
    run_id: str,
    line_id: str,
    quantity: float,
    unit: str,
    company_id: str = "northwind-energy",
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
