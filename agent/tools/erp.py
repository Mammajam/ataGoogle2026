from __future__ import annotations

import csv
import json
from typing import Any

from pipeline.paths import fixtures_dir


def get_erp_activity(company_id: str = "northwind-energy") -> str:
    """Return fixture ERP activity rows for one company / 12 months (JSON string).

    Mock of an SAP/NetSuite export. Scope 2 quantity cells are blank; Scope 3
    purchased-goods rows are spend-only.
    """
    path = fixtures_dir() / "erp_export.csv"
    rows: list[dict[str, Any]] = []
    with path.open(newline="", encoding="utf-8") as handle:
        for raw in csv.DictReader(handle):
            quantity = raw.get("quantity") or ""
            spend = raw.get("spend_gbp") or ""
            rows.append(
                {
                    "period_month": raw["period_month"],
                    "site_id": raw["site_id"],
                    "site_name": raw["site_name"],
                    "ghg_scope": int(raw["ghg_scope"]),
                    "ghg_category": int(raw["ghg_category"]) if raw.get("ghg_category") else None,
                    "activity_type": raw["activity_type"],
                    "activity_name": raw["activity_name"],
                    "quantity": float(quantity) if quantity else None,
                    "unit": raw["unit"] or None,
                    "spend_gbp": float(spend) if spend else None,
                    "vendor": raw["vendor"],
                    "artifact_hint": raw["artifact_hint"],
                    "notes": raw["notes"],
                }
            )
    payload = {
        "company_id": company_id,
        "source": "fixtures/erp_export.csv",
        "row_count": len(rows),
        "rows": rows,
    }
    return json.dumps(payload)


def summarize_erp(company_id: str = "northwind-energy") -> str:
    """Roll ERP rows up by activity for the orchestrator."""
    data = json.loads(get_erp_activity(company_id))
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
    return json.dumps({"company_id": company_id, "activities": list(buckets.values())})
