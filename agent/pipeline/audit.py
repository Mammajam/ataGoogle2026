"""GHG close helpers. Deterministic `run_audit()` assembles from this run's evidence."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pipeline import a2ui
from pipeline.gemini import model_id
from pipeline.activity_map import map_activity
from pipeline.csv_parse import parse_run_tabular
from pipeline.factors_provider import get_provider
from pipeline.store import get_store

MATERIAL_SHARE = 0.05


def _round(value: float, digits: int = 3) -> float:
    return round(value, digits)


def load_company(
    company_id: str,
    *,
    name: str | None = None,
    reporting_year: int | None = None,
    region: str | None = None,
    sector: str | None = None,
) -> dict[str, Any]:
    if not company_id or not str(company_id).strip():
        raise ValueError("company_id is required")
    store = get_store()
    existing = store.read_company(company_id) or {}
    year = reporting_year if reporting_year is not None else existing.get("reporting_year")
    if year is None:
        year = datetime.now(timezone.utc).year
    profile = {
        "company_id": company_id,
        "name": name or existing.get("name") or company_id,
        "reporting_year": int(year),
        "region": region or existing.get("region") or "UK",
        "sector": sector if sector is not None else existing.get("sector"),
    }
    store.write_company(company_id, profile)
    return profile


def _override_map(overrides: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {item["key"]: item for item in overrides if "key" in item}


def _kg(factor: dict[str, Any]) -> float:
    return float(factor.get("kgco2e_per_unit") or 0.0)


def _kwh_from(quantity: float, unit: str) -> float:
    normalized = unit.strip().lower()
    if normalized == "mwh":
        return quantity * 1000.0
    if normalized == "kwh":
        return quantity
    return quantity


def compute_tco2e(quantity: float, unit: str, kg_per_unit: float, activity: str) -> float:
    qty = quantity
    if activity == "electricity":
        qty = _kwh_from(quantity, unit)
    return _round(qty * kg_per_unit / 1000.0)


def apply_quantity_choice(
    line: dict[str, Any], quantity: float, unit: str, factor: dict[str, Any]
) -> dict[str, Any]:
    updated = dict(line)
    activity = str(updated.get("activity_key") or "")
    tco2e = compute_tco2e(quantity, unit, _kg(factor), activity)
    updated["quantity"] = quantity
    updated["unit"] = unit
    updated["tco2e"] = tco2e
    updated["gap_flag"] = None
    updated["confidence"] = max(float(updated.get("confidence") or 0.7), 0.96)
    return updated


def totals_for(lines: list[dict[str, Any]]) -> dict[str, float]:
    by_scope = {1: 0.0, 2: 0.0, 3: 0.0}
    for line in lines:
        if not isinstance(line, dict):
            continue
        scope = line.get("scope", line.get("ghg_scope"))
        if scope is None:
            continue
        scope_n = int(scope)
        if scope_n not in by_scope:
            continue
        by_scope[scope_n] += float(line.get("tco2e") or 0.0)
    return {
        "scope1_tco2e": _round(by_scope[1]),
        "scope2_tco2e": _round(by_scope[2]),
        "scope3_tco2e": _round(by_scope[3]),
        "total_tco2e": _round(sum(by_scope.values())),
    }


def normalize_line(line: dict[str, Any]) -> dict[str, Any]:
    out = dict(line)
    if out.get("scope") is None and out.get("ghg_scope") is not None:
        out["scope"] = out["ghg_scope"]
    return out


def memory_key_for(activity_key: str, field: str = "unit") -> str:
    return f"{activity_key}_{field}"


def _lookup_factor(
    activity: str,
    unit: str,
    company: dict[str, Any],
    method: str | None,
    scope: int | None,
    category: int | None,
) -> dict[str, Any]:
    provider = get_provider()
    return provider.lookup(
        activity=activity,
        unit=unit,
        region=str(company.get("region") or "UK"),
        year=int(company.get("reporting_year") or datetime.now(timezone.utc).year),
        method=method,
        scope=scope,
        category=category,
    )


def _aggregate_erp(rows: list[dict[str, Any]], company: dict[str, Any]) -> dict[str, dict[str, Any]]:
    buckets: dict[str, dict[str, Any]] = {}
    for row in rows:
        raw_name = str(row.get("activity_name") or "")
        key = map_activity(raw_name, company.get("sector"))
        bucket = buckets.setdefault(
            key,
            {
                "activity_key": key,
                "activity": raw_name or key,
                "scope": row.get("ghg_scope") or 3,
                "category": row.get("ghg_category"),
                "quantity": 0.0,
                "unit": row.get("unit") or "",
                "spend": 0.0,
                "quantity_missing": True,
                "vendors": [],
                "source": "erp_export.csv",
            },
        )
        if row.get("quantity") is not None:
            bucket["quantity"] += float(row["quantity"])
            bucket["quantity_missing"] = False
            if row.get("unit"):
                bucket["unit"] = row["unit"]
        if row.get("spend_gbp") is not None:
            bucket["spend"] += float(row["spend_gbp"])
        if row.get("ghg_scope") is not None:
            bucket["scope"] = row["ghg_scope"]
        if row.get("ghg_category") is not None:
            bucket["category"] = row["ghg_category"]
        vendor = row.get("vendor")
        if vendor and vendor not in bucket["vendors"]:
            bucket["vendors"].append(vendor)
    return buckets


def _reading_key(reading: dict[str, Any], company: dict[str, Any]) -> str:
    hint = str(reading.get("activity_hint") or reading.get("activity") or "")
    return map_activity(hint, company.get("sector"))


def assemble_from_evidence(
    *,
    run_id: str,
    company: dict[str, Any],
    extract: dict[str, Any] | None = None,
    artifacts: list[str] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]], dict[str, Any]]:
    store = get_store()
    company_id = str(company["company_id"])
    rows, source = parse_run_tabular(run_id, company_id)
    erp = {
        "company_id": company_id,
        "run_id": run_id,
        "source": source,
        "row_count": len(rows),
        "error": None if source else "no_tabular_artifact",
    }
    override_map = _override_map(store.list_overrides(company_id))
    buckets = _aggregate_erp(rows, company)
    names = artifacts or store.list_artifacts(run_id)

    readings = list((extract or {}).get("readings") or [])
    grouped: dict[str, list[dict[str, Any]]] = {}
    for reading in readings:
        grouped.setdefault(_reading_key(reading, company), []).append(reading)

    for key, group in grouped.items():
        primary = dict(group[0])
        if len(group) > 1 and not primary.get("alternate_unit"):
            second = group[1]
            if str(second.get("unit") or "").lower() != str(primary.get("unit") or "").lower():
                primary["alternate_quantity"] = second.get("quantity")
                primary["alternate_unit"] = second.get("unit")
        qty = primary.get("quantity")
        unit = str(primary.get("unit") or "")
        if key not in buckets:
            buckets[key] = {
                "activity_key": key,
                "activity": key.replace("_", " "),
                "scope": 2 if key == "electricity" else 1 if key in {"diesel", "petrol", "natural_gas"} else 3,
                "category": 6
                if key == "air_travel"
                else 5
                if key == "waste"
                else 4
                if key in {"freight", "road_freight"}
                else (1 if key not in {"electricity", "diesel", "petrol", "natural_gas"} else None),
                "quantity": 0.0,
                "unit": unit,
                "spend": 0.0,
                "quantity_missing": True,
                "vendors": [],
                "source": str(primary.get("source_filename") or ""),
            }
        bucket = buckets[key]
        bucket["reading"] = primary
        if bucket["quantity_missing"] and qty is not None:
            bucket["quantity"] = float(qty)
            bucket["unit"] = unit or bucket["unit"]
            bucket["quantity_missing"] = False
            if primary.get("source_filename"):
                bucket["source"] = primary["source_filename"]

    lines: list[dict[str, Any]] = []
    for key, bucket in buckets.items():
        scope = int(bucket.get("scope") or 3)
        category = bucket.get("category")
        category_n = int(category) if category not in (None, "") else None
        qty = float(bucket.get("quantity") or 0.0)
        unit = str(bucket.get("unit") or "")
        spend = float(bucket.get("spend") or 0.0)
        method = "activity-based"
        if bucket.get("quantity_missing") and spend:
            qty = spend
            unit = "gbp"
            method = "spend-based"
        memory = override_map.get(memory_key_for(key, "unit"))
        gap_flag = None
        assumption = None
        candidates = None
        reading = bucket.get("reading") or {}
        alt_qty = reading.get("alternate_quantity")
        alt_unit = reading.get("alternate_unit")
        if memory:
            qty = float(memory.get("quantity") or qty)
            unit = str(memory.get("unit") or unit)
        elif alt_qty is not None and alt_unit:
            rec = {"quantity": qty, "unit": unit or "kWh"}
            alt = {"quantity": float(alt_qty), "unit": str(alt_unit)}
            candidates = [rec, alt]
            rec_factor = _lookup_factor(key, rec["unit"], company, method, scope, category_n)
            alt_factor = _lookup_factor(key, alt["unit"], company, method, scope, category_n)
            rec_t = compute_tco2e(float(rec["quantity"]), rec["unit"], _kg(rec_factor), key)
            alt_t = compute_tco2e(float(alt["quantity"]), alt["unit"], _kg(alt_factor), key)
            if alt_t >= rec_t:
                qty, unit = float(alt["quantity"]), alt["unit"]
            gap_flag = "unit_conflict"
        elif bucket.get("quantity_missing") and not spend:
            gap_flag = "missing_quantity"
            assumption = "No quantity in tabular evidence and no vision reading."

        factor = _lookup_factor(key, unit or "gbp", company, method, scope, category_n)
        gap_for_factor = gap_flag
        if factor.get("error"):
            gap_for_factor = gap_flag or "factor_missing"
            if gap_flag != "unit_conflict":
                assumption = assumption or f"No factor for {key} {unit}."
            tco2e = 0.0
        else:
            tco2e = compute_tco2e(qty, unit or "unit", _kg(factor), key)

        source_name = bucket.get("source") or (source.split(",")[0] if source else (names[0] if names else ""))
        line = {
            "id": f"s{scope}-{key}" if category_n is None else f"s{scope}-c{category_n}-{key}",
            "scope": scope,
            "category": category_n,
            "activity": bucket.get("activity") or key,
            "activity_key": key,
            "quantity": qty,
            "unit": unit or "unit",
            "tco2e": tco2e,
            "method": method if not factor.get("error") else method,
            "factor_id": factor.get("id") or "",
            "factor_source": factor.get("source") or factor.get("provider") or "",
            "factor_provider": factor.get("provider"),
            "confidence": float(reading.get("confidence") or (0.9 if not gap_for_factor else 0.55)),
            "source": source_name,
            "source_thumb": source_name,
            "gap_flag": gap_for_factor,
            "assumption": assumption,
            "memory_applied": bool(memory),
            "candidates": candidates,
        }
        lines.append(line)

    lines.sort(key=lambda item: (int(item.get("scope") or 9), str(item.get("id"))))
    return lines, override_map, erp


def assemble_lines(
    *,
    company_id: str,
    extract: dict[str, Any] | None = None,
    run_id: str | None = None,
    company: dict[str, Any] | None = None,
    artifacts: list[str] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]], dict[str, Any]]:
    profile = company or load_company(company_id)
    if not run_id:
        return [], _override_map(get_store().list_overrides(company_id)), {
            "error": "no_tabular_artifact",
            "row_count": 0,
        }
    return assemble_from_evidence(
        run_id=run_id,
        company=profile,
        extract=extract,
        artifacts=artifacts,
    )


def attach_material_gate(draft: dict[str, Any]) -> dict[str, Any]:
    """Host-owned A2UI from line candidates — not planted kWh/MWh copy."""
    lines = [normalize_line(item) for item in (draft.get("lines") or [])]
    events = list(draft.get("events") or [])
    widget = None
    a2ui_messages: list[dict[str, Any]] = []
    company = {
        "region": draft.get("region"),
        "reporting_year": draft.get("reporting_year"),
        "company_id": draft.get("company_id"),
    }
    totals = totals_for(lines)

    for line in lines:
        if line.get("gap_flag") not in {"unit_conflict", "quantity_conflict"}:
            continue
        candidates = list(line.get("candidates") or [])
        if len(candidates) < 2:
            continue
        rec, alt = candidates[0], candidates[1]
        factor_rec = _lookup_factor(
            str(line.get("activity_key") or ""),
            str(rec.get("unit") or ""),
            company,
            line.get("method"),
            line.get("scope"),
            line.get("category"),
        )
        factor_alt = _lookup_factor(
            str(line.get("activity_key") or ""),
            str(alt.get("unit") or ""),
            company,
            line.get("method"),
            line.get("scope"),
            line.get("category"),
        )
        rec_t = compute_tco2e(
            float(rec["quantity"]), str(rec["unit"]), _kg(factor_rec), str(line.get("activity_key") or "")
        )
        alt_t = compute_tco2e(
            float(alt["quantity"]), str(alt["unit"]), _kg(factor_alt), str(line.get("activity_key") or "")
        )
        delta_share = abs(rec_t - alt_t) / max(float(totals.get("total_tco2e") or 0.001), 0.001)
        if delta_share <= MATERIAL_SHARE:
            line["gap_flag"] = None
            continue
        run_id = draft["run_id"]
        widget = {
            "kind": "ExtractionConfirm",
            "line_id": line["id"],
            "recommended": rec,
            "alternate": alt,
            "recommended_tco2e": rec_t,
            "alternate_tco2e": alt_t,
            "run_id": run_id,
            "activity": line.get("activity"),
        }
        a2ui_messages = a2ui.extraction_confirm_messages(
            run_id=run_id,
            line_id=line["id"],
            recommended=rec,
            alternate=alt,
            rec_tco2e=rec_t,
            alt_tco2e=alt_t,
            confidence=float(line.get("confidence") or 0.7),
            activity=str(line.get("activity") or line.get("activity_key") or "activity"),
            source=str(line.get("source") or "evidence"),
        )
        events.append(
            {
                "step": "gate",
                "message": (
                    f"Material unit conflict on {line.get('activity')} "
                    f"({rec.get('unit')} vs {alt.get('unit')}) — emitting A2UI ExtractionConfirm."
                ),
            }
        )
        break

    policy_keys = list(draft.get("policy_keys") or [])
    gaps = {str(item.get("gap_flag") or "") for item in lines}
    draft["lines"] = lines
    draft["totals"] = totals_for(lines)
    draft["widget"] = widget
    draft["a2ui"] = a2ui_messages
    draft["events"] = events
    if widget:
        draft["status"] = "needs_confirmation"
    elif gaps & {"missing_quantity", "factor_missing", "unmapped_activity"} or (
        not lines
    ):
        draft["status"] = "incomplete"
    else:
        draft["status"] = "complete"
    draft["policy_applied"] = bool(policy_keys) and widget is None
    return draft


def empty_draft(
    run_id: str,
    company_id: str,
    artifacts: list[str] | None = None,
    company: dict[str, Any] | None = None,
) -> dict[str, Any]:
    profile = company or load_company(company_id)
    return {
        "run_id": run_id,
        "company_id": company_id,
        "company_name": profile.get("name", company_id),
        "reporting_year": profile.get("reporting_year"),
        "region": profile.get("region"),
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "status": "in_progress",
        "lines": [],
        "totals": totals_for([]),
        "artifacts": artifacts or [],
        "erp_row_count": 0,
        "policy_applied": False,
        "policy_keys": [],
        "widget": None,
        "a2ui": [],
        "events": [],
        "engine": "adk",
        "scopes_populated": [],
    }


def persist_line(run_id: str, line: dict[str, Any]) -> dict[str, Any]:
    store = get_store()
    company_id = str(line.get("company_id") or (store.read_draft(run_id) or {}).get("company_id") or "")
    draft = store.read_draft(run_id) or empty_draft(run_id, company_id or "unknown")
    normalized = normalize_line(line)
    lines = [item for item in (draft.get("lines") or []) if item.get("id") != normalized.get("id")]
    lines.append(normalized)
    draft["lines"] = lines
    draft["totals"] = totals_for(lines)
    draft["scopes_populated"] = sorted(
        {
            int(item["scope"])
            for item in lines
            if isinstance(item, dict) and item.get("scope") is not None
        }
    )
    store.write_draft(run_id, draft)
    return draft


def persist_draft_lines(
    run_id: str,
    company_id: str,
    lines: list[dict[str, Any]],
    *,
    artifacts: list[str] | None = None,
    events: list[dict[str, Any]] | None = None,
    engine: str = "adk",
    company: dict[str, Any] | None = None,
) -> dict[str, Any]:
    store = get_store()
    existing = store.read_draft(run_id) or empty_draft(run_id, company_id, artifacts, company)
    normalized = [normalize_line(line) for line in lines]
    override_map = _override_map(store.list_overrides(company_id))
    existing.update(
        {
            "company_id": company_id,
            "lines": normalized,
            "totals": totals_for(normalized),
            "artifacts": artifacts if artifacts is not None else existing.get("artifacts") or [],
            "events": events if events is not None else existing.get("events") or [],
            "engine": engine,
            "policy_keys": list(override_map.keys()),
            "scopes_populated": sorted(
                {int(line["scope"]) for line in normalized if line.get("scope") is not None}
            ),
            "widget": None,
            "a2ui": [],
        }
    )
    store.write_draft(run_id, existing)
    return existing


def run_audit(
    *,
    company_id: str,
    company_name: str | None = None,
    reporting_year: int | None = None,
    region: str | None = None,
    filenames: list[str] | None = None,
    extract: dict[str, Any] | None = None,
    run_id: str | None = None,
    engine: str = "deterministic",
    classified: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if not company_id:
        raise ValueError("company_id is required")
    if not run_id:
        raise ValueError("run_id is required")
    store = get_store()
    company = load_company(
        company_id, name=company_name, reporting_year=reporting_year, region=region
    )
    artifacts = filenames or store.list_artifacts(run_id)
    events = [
        {"step": "memory", "message": "Loaded company overrides."},
        {"step": "parse", "message": "Classified uploaded evidence by type."},
    ]
    if classified:
        roles = ", ".join(f"{item['filename']}={item['role']}" for item in classified)
        events.append({"step": "classify", "message": roles or "No artifacts classified."})
    if extract and extract.get("source") == "unavailable":
        events.append(
            {
                "step": "vision_unavailable",
                "message": extract.get("reason") or "Vision/Vertex unavailable — tabular evidence only.",
            }
        )
    elif extract and extract.get("source") == "vertex":
        events.append(
            {
                "step": "extract",
                "message": f"Vision extract confidence {float(extract.get('confidence') or 0):.0%}.",
            }
        )

    lines, override_map, erp = assemble_from_evidence(
        run_id=run_id, company=company, extract=extract, artifacts=artifacts
    )
    events.append({"step": "erp", "message": f"Read {erp.get('row_count', 0)} ERP activity rows."})
    if erp.get("error"):
        events.append({"step": "erp", "message": "No tabular artifact on this run."})

    factor_source = next((line.get("factor_provider") for line in lines if line.get("factor_provider")), "fixture")
    events.append({"step": "factor_source", "message": f"Emission factors from {factor_source}."})

    draft = {
        "run_id": run_id,
        "company_id": company_id,
        "company_name": company.get("name", company_id),
        "reporting_year": company.get("reporting_year"),
        "region": company.get("region"),
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "lines": lines,
        "totals": totals_for(lines),
        "artifacts": artifacts,
        "erp_row_count": erp.get("row_count", 0),
        "policy_keys": list(override_map.keys()),
        "events": events,
        "engine": engine,
        "model": model_id() if engine == "adk" else "deterministic-evidence",
        "scopes_populated": sorted({int(line["scope"]) for line in lines if line.get("scope") is not None}),
    }
    draft = attach_material_gate(draft)
    store.write_draft(run_id, draft)
    store.write_evidence(
        run_id,
        {
            "company_id": company_id,
            "artifacts": artifacts,
            "classified": classified or [],
            "extractions": extract or {},
            "events": draft["events"],
        },
    )
    draft["events"] = list(draft["events"]) + [{"step": "write", "message": f"Wrote draft {run_id}."}]
    store.write_draft(run_id, draft)
    return draft


def confirm_extraction(
    *,
    run_id: str,
    line_id: str,
    quantity: float,
    unit: str,
    company_id: str,
) -> dict[str, Any]:
    store = get_store()
    draft = store.read_draft(run_id)
    if not draft:
        raise KeyError(f"Unknown run_id {run_id}")
    company = load_company(company_id)

    lines = []
    matched = None
    for line in draft["lines"]:
        if line["id"] == line_id:
            factor = _lookup_factor(
                str(line.get("activity_key") or ""),
                unit,
                company,
                line.get("method"),
                line.get("scope"),
                line.get("category"),
            )
            line = apply_quantity_choice(line, quantity, unit, factor)
            line["memory_applied"] = False
            line["candidates"] = None
            matched = line
        lines.append(line)

    activity_key = str((matched or {}).get("activity_key") or "activity")
    override = store.upsert_override(
        company_id,
        {
            "key": memory_key_for(activity_key, "unit"),
            "line_id": line_id,
            "field": "unit",
            "quantity": quantity,
            "unit": unit,
            "source": "extraction_confirm",
        },
    )
    updated = {
        **draft,
        "lines": lines,
        "totals": totals_for(lines),
        "status": "complete",
        "widget": None,
        "a2ui": [],
        "policy_applied": True,
        "policy_keys": [override["key"]],
        "last_confirmation": {
            "line_id": line_id,
            "quantity": quantity,
            "unit": unit,
        },
        "events": list(draft.get("events") or [])
        + [
            {
                "step": "confirm",
                "message": f"Persisted {unit} override and recomputed {line_id}.",
            }
        ],
    }
    store.write_draft(run_id, updated)
    return updated
