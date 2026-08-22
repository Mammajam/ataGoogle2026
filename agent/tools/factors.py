from __future__ import annotations

import json

from pipeline.paths import fixtures_dir


def load_factors() -> list[dict]:
    payload = json.loads((fixtures_dir() / "factors.json").read_text(encoding="utf-8"))
    return payload["factors"]


def lookup_factor(
    activity: str,
    unit: str,
    region: str = "UK",
    year: int = 2025,
    method: str | None = None,
) -> str:
    """Look up a mock carbon emission factor (JSON string)."""
    matches = []
    for row in load_factors():
        if row["activity"] != activity:
            continue
        if region and row.get("region") != region:
            continue
        if year and row.get("year") != year:
            continue
        if method and row.get("method") != method:
            continue
        # Electricity factors are stored per kWh even when the activity unit is MWh.
        if activity != "electricity" and unit and row.get("unit") != unit.lower() and row.get("unit") != unit:
            continue
        matches.append(row)
    if not matches:
        return json.dumps(
            {
                "error": "factor_not_found",
                "activity": activity,
                "unit": unit,
                "region": region,
                "year": year,
                "method": method,
            }
        )
    chosen = matches[0]
    return json.dumps(chosen)
