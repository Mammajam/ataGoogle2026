"""Parse uploaded ERP CSVs using a published column-alias map."""

from __future__ import annotations

import csv
import io
from typing import Any

from pipeline.classify import classify_filename
from pipeline.erp_provider import fetch_live_erp, merge_tabular
from pipeline.store import get_store

COLUMN_ALIASES: dict[str, tuple[str, ...]] = {
    "period": ("period_month", "period", "month", "date", "reporting_period"),
    "site_id": ("site_id", "site", "location_id"),
    "site_name": ("site_name", "location", "site"),
    "scope": ("ghg_scope", "scope", "ghg_scope_id"),
    "category": ("ghg_category", "category", "ghg_cat"),
    "activity_type": ("activity_type", "type", "source_type"),
    "activity_name": ("activity_name", "activity", "activity_key", "fuel", "description"),
    "quantity": ("quantity", "qty", "amount_qty", "volume"),
    "unit": ("unit", "uom", "quantity_unit"),
    "spend": ("spend_gbp", "spend", "amount", "spend_usd", "value", "cost"),
    "currency": ("currency", "ccy"),
    "vendor": ("vendor", "supplier", "counterparty"),
    "artifact_hint": ("artifact_hint", "source", "evidence"),
    "notes": ("notes", "comment", "remark"),
}


def _norm_header(name: str) -> str:
    return name.strip().lower().replace(" ", "_")


def map_headers(fieldnames: list[str] | None) -> dict[str, str]:
    found: dict[str, str] = {}
    headers = {_norm_header(item): item for item in (fieldnames or []) if item}
    for canonical, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in headers:
                found[canonical] = headers[alias]
                break
    return found


def _to_float(value: str | None) -> float | None:
    raw = (value or "").strip().replace(",", "")
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def _to_int(value: str | None) -> int | None:
    raw = (value or "").strip()
    if not raw:
        return None
    try:
        return int(float(raw))
    except ValueError:
        return None


def parse_csv_bytes(data: bytes) -> list[dict[str, Any]]:
    text = data.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    mapping = map_headers(list(reader.fieldnames or []))
    if "scope" not in mapping or "activity_name" not in mapping:
        return []
    if "period" not in mapping:
        return []
    rows: list[dict[str, Any]] = []
    for raw in reader:
        activity = (raw.get(mapping["activity_name"]) or "").strip()
        if not activity:
            continue
        quantity = _to_float(raw.get(mapping["quantity"])) if "quantity" in mapping else None
        spend = _to_float(raw.get(mapping["spend"])) if "spend" in mapping else None
        unit = (raw.get(mapping["unit"]) or "").strip() if "unit" in mapping else ""
        if quantity is None and spend is None:
            continue
        rows.append(
            {
                "period_month": (raw.get(mapping["period"]) or "").strip(),
                "site_id": (raw.get(mapping["site_id"]) or "").strip() if "site_id" in mapping else "",
                "site_name": (raw.get(mapping["site_name"]) or "").strip() if "site_name" in mapping else "",
                "ghg_scope": _to_int(raw.get(mapping["scope"])),
                "ghg_category": _to_int(raw.get(mapping["category"])) if "category" in mapping else None,
                "activity_type": (raw.get(mapping["activity_type"]) or "").strip()
                if "activity_type" in mapping
                else "",
                "activity_name": activity,
                "quantity": quantity,
                "unit": unit or None,
                "spend_gbp": spend,
                "currency": (raw.get(mapping["currency"]) or "GBP").strip()
                if "currency" in mapping
                else "GBP",
                "vendor": (raw.get(mapping["vendor"]) or "").strip() if "vendor" in mapping else "",
                "artifact_hint": (raw.get(mapping["artifact_hint"]) or "").strip()
                if "artifact_hint" in mapping
                else "",
                "notes": (raw.get(mapping["notes"]) or "").strip() if "notes" in mapping else "",
            }
        )
    return rows


def parse_run_tabular(
    run_id: str, company_id: str | None = None
) -> tuple[list[dict[str, Any]], str | None]:
    store = get_store()
    names = store.list_artifacts(run_id)
    merged: list[dict[str, Any]] = []
    sources: list[str] = []
    for name in names:
        if classify_filename(name) != "erp_tabular":
            continue
        data = store.read_artifact(run_id, name)
        if not data:
            continue
        rows = parse_csv_bytes(data)
        if rows:
            merged.extend(rows)
            sources.append(name)
    live_rows, live_source = fetch_live_erp(company_id or "", run_id)
    if live_rows:
        merged = merge_tabular(merged, live_rows)
        if live_source:
            sources.append(live_source)
    if not merged:
        return [], None
    return merged, ",".join(sources)
