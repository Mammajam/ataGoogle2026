from __future__ import annotations

import json

from pipeline.factors_provider import FixtureProvider, get_provider
from pipeline.paths import fixtures_dir


def load_factors() -> list[dict]:
    payload = json.loads((fixtures_dir() / "factors.json").read_text(encoding="utf-8"))
    return payload["factors"]


def lookup_factor(
    activity: str,
    unit: str,
    region: str,
    year: int,
    method: str | None = None,
) -> str:
    """Look up an emission factor (JSON string). Region and year come from the company close."""
    provider = get_provider()
    result = provider.lookup(activity, unit, region, year, method)
    return json.dumps(result)


def fixture_catalog() -> FixtureProvider:
    return FixtureProvider()
