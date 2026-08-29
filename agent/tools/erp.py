from __future__ import annotations

import json
from typing import Any

from pipeline.csv_parse import parse_run_tabular


def get_erp_activity(run_id: str, company_id: str) -> str:
    """Return this run's uploaded tabular activity rows (JSON string)."""
    rows, source = parse_run_tabular(run_id, company_id)
    if source is None:
        return json.dumps(
            {"error": "no_tabular_artifact", "run_id": run_id, "company_id": company_id, "row_count": 0, "rows": []}
        )
    payload = {
        "company_id": company_id,
        "run_id": run_id,
        "source": source,
        "row_count": len(rows),
        "rows": rows,
    }
    return json.dumps(payload)


def summarize_erp(run_id: str, company_id: str) -> str:
    """Roll this run's ERP rows up by activity."""
    data = json.loads(get_erp_activity(run_id, company_id))
    if data.get("error"):
        return json.dumps(data)
    buckets: dict[str, dict[str, Any]] = {}
    for row in data["rows"]:
        key = row["activity_name"]
        bucket = buckets.setdefault(
            key,
            {
                "activity": key,
                "scope": row["ghg_scope"],
                "category": row["ghg_category"],
                "quantity": 0.0,
                "unit": row["unit"],
                "spend_gbp": 0.0,
                "quantity_missing": False,
            },
        )
        if row["quantity"] is None:
            bucket["quantity_missing"] = True
        else:
            bucket["quantity"] += row["quantity"]
        if row["spend_gbp"] is not None:
            bucket["spend_gbp"] += row["spend_gbp"]
    return json.dumps({"company_id": company_id, "run_id": run_id, "activities": list(buckets.values())})
