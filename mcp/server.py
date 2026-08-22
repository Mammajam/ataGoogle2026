"""Thin FastMCP HTTP wrappers of the same ERP + factor functions the ADK agent uses."""

from __future__ import annotations

import sys
from pathlib import Path

AGENT_DIR = Path(__file__).resolve().parents[1] / "agent"
sys.path.insert(0, str(AGENT_DIR))

from tools.erp import get_erp_activity, summarize_erp  # noqa: E402
from tools.factors import lookup_factor  # noqa: E402
from tools.inventory import apply_extraction_confirm, get_draft, write_draft  # noqa: E402
from tools.memory import load_company_overrides  # noqa: E402

try:
    from fastmcp import FastMCP
except ImportError as exc:  # pragma: no cover
    raise SystemExit("pip install -r mcp/requirements.txt") from exc

mcp = FastMCP(
    "greenchain-tools",
    instructions=(
        "MCP-compatible tool interface for GreenChain. Same functions as ADK FunctionTools: "
        "ERP activity, emission factors, draft write, and company memory."
    ),
)


@mcp.tool()
def erp_get_activity(company_id: str = "northwind-energy") -> str:
    """Activity data: fuel, electricity, purchased goods for one company / 12 months."""
    return get_erp_activity(company_id)


@mcp.tool()
def erp_summarize(company_id: str = "northwind-energy") -> str:
    """Roll ERP rows up by activity."""
    return summarize_erp(company_id)


@mcp.tool()
def factors_lookup(
    activity: str,
    unit: str,
    region: str = "UK",
    year: int = 2025,
    method: str | None = None,
) -> str:
    """Emission factor by fuel, grid, spend category, region, year."""
    return lookup_factor(activity, unit, region, year, method)


@mcp.tool()
def inventory_write_draft(company_id: str = "northwind-energy") -> str:
    """Write a complete draft inventory. Never ask before this exists."""
    return write_draft(company_id)


@mcp.tool()
def inventory_get_draft(run_id: str) -> str:
    """Read a draft by run id."""
    return get_draft(run_id)


@mcp.tool()
def memory_load(company_id: str = "northwind-energy") -> str:
    """Company override memory."""
    return load_company_overrides(company_id)


@mcp.tool()
def inventory_confirm(
    run_id: str,
    line_id: str,
    quantity: float,
    unit: str,
    company_id: str = "northwind-energy",
) -> str:
    """Apply an ExtractionConfirm answer and persist policy."""
    return apply_extraction_confirm(run_id, line_id, quantity, unit, company_id)


if __name__ == "__main__":
    # HTTP transport so the architecture diagram is an honest MCP server, not a fake label.
    mcp.run(transport="http", host="0.0.0.0", port=int(__import__("os").environ.get("PORT", "8081")))
