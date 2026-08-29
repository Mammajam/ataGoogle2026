"""Pluggable emission-factor lookup. Catalog supplies kgCO2e, never inventory lines."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Protocol

from pipeline.paths import fixtures_dir

CLIMATIQ_BASE = (os.environ.get("CLIMATIQ_API_URL") or "https://api.climatiq.io").rstrip("/")
CLIMATIQ_DATA_VERSION = os.environ.get("CLIMATIQ_DATA_VERSION") or "^21"


def _urlopen(req: urllib.request.Request, timeout: int = 10):
    return urllib.request.urlopen(req, timeout=timeout)


class FactorProvider(Protocol):
    def lookup(
        self,
        activity: str,
        unit: str,
        region: str,
        year: int,
        method: str | None = None,
        scope: int | None = None,
        category: int | None = None,
    ) -> dict[str, Any]: ...


def _unit_ok(row: dict[str, Any], activity: str, unit: str) -> bool:
    wanted = (unit or "").strip().lower()
    have = str(row.get("unit") or "").strip().lower()
    if activity == "electricity":
        return have in {"kwh", "mwh", wanted} or not wanted
    if not wanted:
        return True
    return have == wanted or have in {wanted, wanted.rstrip("s")}


class FixtureProvider:
    def __init__(self) -> None:
        path = fixtures_dir() / "factors.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.rows: list[dict[str, Any]] = list(payload.get("factors") or [])

    def lookup(
        self,
        activity: str,
        unit: str,
        region: str,
        year: int,
        method: str | None = None,
        scope: int | None = None,
        category: int | None = None,
    ) -> dict[str, Any]:
        scored: list[tuple[int, dict[str, Any]]] = []
        for row in self.rows:
            if row.get("activity") != activity:
                continue
            if not _unit_ok(row, activity, unit):
                continue
            score = 0
            if region and row.get("region") == region:
                score += 2
            if year and int(row.get("year") or 0) == int(year):
                score += 2
            if method and row.get("method") == method:
                score += 1
            if scope is not None and row.get("scope") == scope:
                score += 1
            if category is not None and row.get("category") == category:
                score += 1
            scored.append((score, row))
        if not scored:
            return {
                "error": "factor_not_found",
                "activity": activity,
                "unit": unit,
                "region": region,
                "year": year,
                "provider": "fixture",
            }
        scored.sort(key=lambda item: item[0], reverse=True)
        row = dict(scored[0][1])
        row["provider"] = "fixture"
        return row


class HttpFactorProvider:
    def __init__(self, url: str, token: str | None = None) -> None:
        self.url = url.rstrip("/")
        self.token = token
        self._fallback = FixtureProvider()

    def lookup(
        self,
        activity: str,
        unit: str,
        region: str,
        year: int,
        method: str | None = None,
        scope: int | None = None,
        category: int | None = None,
    ) -> dict[str, Any]:
        body = json.dumps(
            {
                "activity": activity,
                "unit": unit,
                "region": region,
                "year": year,
                "method": method,
                "scope": scope,
                "category": category,
            }
        ).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        req = urllib.request.Request(self.url, data=body, headers=headers, method="POST")
        try:
            with _urlopen(req, timeout=8) as res:
                payload = json.loads(res.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError) as exc:
            fallback = self._fallback.lookup(activity, unit, region, year, method, scope, category)
            fallback["http_error"] = str(exc)
            fallback["provider"] = fallback.get("provider") or "fixture"
            return fallback
        if not isinstance(payload, dict) or payload.get("error"):
            fallback = self._fallback.lookup(activity, unit, region, year, method, scope, category)
            fallback["http_error"] = payload.get("error") if isinstance(payload, dict) else "invalid_response"
            return fallback
        payload["provider"] = "http"
        return payload


def climatiq_api_key() -> str:
    return (
        os.environ.get("CLIMATIQ_API_KEY")
        or os.environ.get("GREENCHAIN_CLIMATIQ_KEY")
        or ""
    ).strip()


def _climatiq_region(region: str) -> str:
    raw = (region or "").strip().upper()
    return {"UK": "GB", "GBR": "GB", "UNITED KINGDOM": "GB"}.get(raw, raw or "GB")


def _climatiq_parameters(unit: str) -> dict[str, Any]:
    u = (unit or "").strip().lower()
    if u in {"kwh"}:
        return {"energy": 1, "energy_unit": "kWh"}
    if u in {"mwh"}:
        return {"energy": 1, "energy_unit": "MWh"}
    if u in {"litre", "liter", "litres", "liters", "l"}:
        return {"volume": 1, "volume_unit": "l"}
    if u in {"kg"}:
        return {"weight": 1, "weight_unit": "kg"}
    if u in {"t", "tonne", "tonnes", "ton"}:
        return {"weight": 1, "weight_unit": "t"}
    if u in {"gbp", "usd", "eur"}:
        return {"money": 1, "money_unit": u}
    if u in {"km"}:
        return {"distance": 1, "distance_unit": "km"}
    return {"energy": 1, "energy_unit": "kWh"}


class ClimatiqProvider:
    """Live Climatiq estimate (1 activity unit → kgCO2e). Fixture is last-resort fallback."""

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        self._fallback = FixtureProvider()
        self._search_cache: dict[str, dict[str, Any]] = {}

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def _request(self, method: str, url: str, body: bytes | None = None) -> dict[str, Any]:
        req = urllib.request.Request(url, data=body, headers=self._headers(), method=method)
        with _urlopen(req, timeout=10) as res:
            return json.loads(res.read().decode("utf-8"))

    def _search(self, activity: str, region: str, year: int, unit: str) -> dict[str, Any] | None:
        cache_key = f"{activity}|{region}|{year}|{unit}"
        if cache_key in self._search_cache:
            return self._search_cache[cache_key]
        query = urllib.parse.urlencode(
            {
                "query": activity.replace("_", " "),
                "data_version": CLIMATIQ_DATA_VERSION,
                "region": _climatiq_region(region),
                "year": year,
                "results_per_page": 1,
            }
        )
        try:
            payload = self._request("GET", f"{CLIMATIQ_BASE}/data/v1/search?{query}")
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError):
            return None
        results = payload.get("results") if isinstance(payload, dict) else None
        if not results:
            return None
        factor = results[0] if isinstance(results[0], dict) else None
        if factor:
            self._search_cache[cache_key] = factor
        return factor

    def lookup(
        self,
        activity: str,
        unit: str,
        region: str,
        year: int,
        method: str | None = None,
        scope: int | None = None,
        category: int | None = None,
    ) -> dict[str, Any]:
        factor = self._search(activity, region, year, unit)
        if not factor or not factor.get("activity_id"):
            fallback = self._fallback.lookup(activity, unit, region, year, method, scope, category)
            fallback["provider"] = fallback.get("provider") or "fixture"
            fallback["climatiq_error"] = "no_emission_factor"
            return fallback
        body = json.dumps(
            {
                "emission_factor": {
                    "id": factor.get("id"),
                    "activity_id": factor.get("activity_id"),
                    "data_version": factor.get("data_version") or CLIMATIQ_DATA_VERSION,
                    "source": factor.get("source"),
                    "region": factor.get("region") or _climatiq_region(region),
                    "year": factor.get("year") or year,
                },
                "parameters": _climatiq_parameters(unit),
            }
        ).encode("utf-8")
        try:
            payload = self._request("POST", f"{CLIMATIQ_BASE}/data/v1/estimate", body)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError) as exc:
            fallback = self._fallback.lookup(activity, unit, region, year, method, scope, category)
            fallback["http_error"] = str(exc)
            fallback["provider"] = fallback.get("provider") or "fixture"
            return fallback
        co2e = payload.get("co2e")
        co2e_unit = str(payload.get("co2e_unit") or "kg").lower()
        try:
            kg = float(co2e or 0)
        except (TypeError, ValueError):
            kg = 0.0
        if co2e_unit in {"t", "tonne", "tonnes"}:
            kg *= 1000.0
        ef = payload.get("emission_factor") if isinstance(payload.get("emission_factor"), dict) else factor
        return {
            "id": str((ef or {}).get("id") or factor.get("id") or factor.get("activity_id")),
            "activity": activity,
            "unit": unit,
            "region": region,
            "year": int((ef or {}).get("year") or year),
            "kgco2e_per_unit": kg,
            "source": str((ef or {}).get("source") or "Climatiq"),
            "method": method or "activity-based",
            "scope": scope,
            "category": category,
            "provider": "climatiq",
            "activity_id": factor.get("activity_id"),
        }


def get_provider() -> FactorProvider:
    key = climatiq_api_key()
    if key:
        return ClimatiqProvider(key)
    url = (os.environ.get("GREENCHAIN_FACTOR_URL") or "").strip()
    if url:
        token = (
            os.environ.get("GREENCHAIN_FACTOR_TOKEN") or os.environ.get("GREENCHAIN_FACTOR_API_KEY") or ""
        ).strip() or None
        return HttpFactorProvider(url, token)
    return FixtureProvider()


def factor_status() -> dict[str, Any]:
    key = bool(climatiq_api_key())
    url = (os.environ.get("GREENCHAIN_FACTOR_URL") or "").strip()
    if key:
        return {"live": True, "ok": True, "provider": "climatiq"}
    if url:
        return {"live": True, "ok": True, "provider": "http", "url": url}
    return {
        "live": False,
        "ok": True,
        "provider": "fixture",
        "note": "Offline catalog. Set CLIMATIQ_API_KEY for live factors.",
    }


get_factor_provider = get_provider
