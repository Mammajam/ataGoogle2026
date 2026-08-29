"""Thin FastMCP HTTP wrappers of primitive ERP, factor, inventory, and memory tools."""

from __future__ import annotations

import sys
from pathlib import Path

AGENT_DIR = Path(__file__).resolve().parents[1] / "agent"
sys.path.insert(0, str(AGENT_DIR))

from tools.erp import get_erp_activity, summarize_erp  # noqa: E402
from tools.factors import lookup_factor  # noqa: E402
from tools.inventory import (  # noqa: E402
    apply_extraction_confirm,
    get_draft,
    persist_draft_tool,
    persist_line_tool,
)
from tools.memory import load_company_overrides, save_company_override  # noqa: E402

try:
    from fastmcp import FastMCP
except ImportError as exc:  # pragma: no cover
    raise SystemExit("pip install -r mcp/requirements.txt") from exc

mcp = FastMCP(
    "greenchain-tools",
    instructions=(
        "Primitive GreenChain tools: run-scoped ERP, emission factors, persist inventory "
        "lines/drafts, and company memory. Pass run_id and company_id. Do not run a full audit close here."
    ),
)


@mcp.tool()
def erp_get_activity(run_id: str, company_id: str) -> str:
    """Activity data from this run's uploaded CSV and/or live ERP."""
    return get_erp_activity(run_id, company_id)


@mcp.tool()
def erp_summarize(run_id: str, company_id: str) -> str:
    """Roll this run's ERP rows up by activity."""
    return summarize_erp(run_id, company_id)


@mcp.tool()
def factors_lookup(
    activity: str,
    unit: str,
    region: str,
    year: int,
    method: str | None = None,
) -> str:
    """Emission factor by activity, unit, region, and year supplied by the caller."""
    return lookup_factor(activity, unit, region, int(year), method)


@mcp.tool()
def inventory_persist_line(run_id: str, line_json: str) -> str:
    """Merge one inventory line. No extract, no A2UI."""
    return persist_line_tool(run_id, line_json)


@mcp.tool()
def inventory_persist_draft(
    run_id: str,
    company_id: str,
    lines_json: str = "[]",
) -> str:
    """Save line set + totals only. Host attaches A2UI after the agent turn."""
    return persist_draft_tool(run_id, company_id, lines_json)


@mcp.tool()
def inventory_get_draft(run_id: str) -> str:
    """Read a draft by run id."""
    return get_draft(run_id)


@mcp.tool()
def memory_load(company_id: str) -> str:
    """Company override memory."""
    return load_company_overrides(company_id)


@mcp.tool()
def memory_save(
    key: str,
    line_id: str,
    field: str,
    value: str,
    company_id: str,
    quantity: float | None = None,
    unit: str | None = None,
) -> str:
    """Persist a company policy override."""
    return save_company_override(key, line_id, field, value, quantity, unit, company_id)


@mcp.tool()
def inventory_confirm(
    run_id: str,
    line_id: str,
    quantity: float,
    unit: str,
    company_id: str,
) -> str:
    """Apply an ExtractionConfirm answer and persist policy."""
    return apply_extraction_confirm(run_id, line_id, quantity, unit, company_id)


if __name__ == "__main__":
    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=int(__import__("os").environ.get("PORT", "8081")),
    )
