"""Live ERP activity pull. Uploaded CSV still overlays this run when present."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from pipeline.activity_map import map_activity


def erp_url() -> str:
    return (os.environ.get("GREENCHAIN_ERP_URL") or "").strip().rstrip("/")


def erp_token() -> str:
    return (os.environ.get("GREENCHAIN_ERP_TOKEN") or os.environ.get("GREENCHAIN_ERP_API_KEY") or "").strip()


def erp_live_configured() -> bool:
    return bool(erp_url())


def erp_status() -> dict[str, Any]:
    url = erp_url()
    if not url:
        return {"live": False, "ok": True, "provider": "upload", "url": None}
    return {"live": True, "ok": True, "provider": "http", "url": url, "auth": bool(erp_token())}


def _normalize_row(raw: dict[str, Any]) -> dict[str, Any] | None:
    activity = str(
        raw.get("activity_name") or raw.get("activity") or raw.get("activity_key") or ""
    ).strip()
    if not activity:
        return None
    quantity = raw.get("quantity")
    if quantity is None:
        quantity = raw.get("qty")
    spend = raw.get("spend_gbp")
    if spend is None:
        spend = raw.get("spend") or raw.get("amount")
    try:
        quantity_n = float(quantity) if quantity not in (None, "") else None
    except (TypeError, ValueError):
        quantity_n = None
    try:
        spend_n = float(spend) if spend not in (None, "") else None
    except (TypeError, ValueError):
        spend_n = None
    if quantity_n is None and spend_n is None:
        return None
    scope = raw.get("ghg_scope")
    if scope is None:
        scope = raw.get("scope")
    category = raw.get("ghg_category")
    if category is None:
        category = raw.get("category")
    try:
        scope_n = int(scope) if scope not in (None, "") else None
    except (TypeError, ValueError):
        scope_n = None
    try:
        category_n = int(category) if category not in (None, "") else None
    except (TypeError, ValueError):
        category_n = None
    return {
        "period_month": str(raw.get("period_month") or raw.get("period") or raw.get("month") or "").strip(),
        "site_id": str(raw.get("site_id") or ""),
        "site_name": str(raw.get("site_name") or ""),
        "ghg_scope": scope_n,
        "ghg_category": category_n,
        "activity_type": str(raw.get("activity_type") or ""),
        "activity_name": activity,
        "quantity": quantity_n,
        "unit": str(raw.get("unit") or raw.get("uom") or "") or None,
        "spend_gbp": spend_n,
        "currency": str(raw.get("currency") or "GBP"),
        "vendor": str(raw.get("vendor") or ""),
        "artifact_hint": str(raw.get("artifact_hint") or "erp"),
        "notes": str(raw.get("notes") or ""),
        "source": "live_erp",
    }


def fetch_live_erp(company_id: str, run_id: str | None = None) -> tuple[list[dict[str, Any]], str | None]:
    """GET GREENCHAIN_ERP_URL?company_id&year&region&run_id. Returns normalized rows."""
    url = erp_url()
    if not url or not company_id:
        return [], None
    from pipeline.store import get_store

    profile = get_store().read_company(company_id) or {}
    query = urllib.parse.urlencode(
        {
            "company_id": company_id,
            "year": profile.get("reporting_year") or "",
            "region": profile.get("region") or "",
            "run_id": run_id or "",
        }
    )
    headers = {"Accept": "application/json"}
    token = erp_token()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(f"{url}?{query}", headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=12) as res:
            payload = json.loads(res.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError):
        return [], None
    raw_rows = payload.get("rows") if isinstance(payload, dict) else payload
    if not isinstance(raw_rows, list):
        return [], None
    rows = [item for item in (_normalize_row(row) for row in raw_rows if isinstance(row, dict)) if item]
    if not rows:
        return [], None
    return rows, "live_erp"


def merge_tabular(
    csv_rows: list[dict[str, Any]],
    live_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """CSV wins per activity_key; live ERP fills activities the upload does not cover."""
    if not live_rows:
        return csv_rows
    if not csv_rows:
        return live_rows
    csv_keys = {map_activity(str(row.get("activity_name") or "")) for row in csv_rows}
    extra = [
        row for row in live_rows if map_activity(str(row.get("activity_name") or "")) not in csv_keys
    ]
    return csv_rows + extra
