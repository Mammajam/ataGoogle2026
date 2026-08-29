from __future__ import annotations

import json

from pipeline.store import get_store


def load_company_overrides(company_id: str) -> str:
    """Load remembered audit policy for this company."""
    items = get_store().list_overrides(company_id)
    return json.dumps({"company_id": company_id, "overrides": items, "count": len(items)})


def save_company_override(
    key: str,
    line_id: str,
    field: str,
    value: str,
    quantity: float | None,
    unit: str | None,
    company_id: str,
) -> str:
    """Store a widget answer as company policy for the next silent rerun."""
    payload = {
        "key": key,
        "line_id": line_id,
        "field": field,
        "value": value,
        "quantity": quantity,
        "unit": unit,
        "source": "agent_tool",
    }
    saved = get_store().upsert_override(company_id, payload)
    return json.dumps(saved)
