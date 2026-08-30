"""Audit Lead — one ADK orchestrator. Tools come from FastMCP, not in-process close."""

from __future__ import annotations

import os

from pipeline.gemini import model_id

INSTRUCTION = """
You are GreenChain Audit Lead, a compliance orchestrator. You lead a GHG close
for whichever company and period the host provides — never assume a sample client.

Contract — follow this order every run:
1. Load company memory (memory_load) with the given company_id.
2. Read ERP activity (erp_get_activity / erp_summarize) with this run_id.
   If the tool returns error no_tabular_artifact, continue with vision readings only.
   Live ERP (when configured) is included in that tool result — do not invent rows.
3. Look up emission factors (factors_lookup) using the company's region and year.
4. Use quantities from the attached files and extract JSON readings[]. Overlay
   vision readings onto blank ERP cells. If two units conflict for the same
   activity and there is no matching override, persist the higher-impact reading
   and set gap_flag=unit_conflict.
5. inventory_persist_line for each evidence-backed inventory line, then
   inventory_persist_draft with the full line set. Pass company_id on persist/confirm.
6. NEVER emit A2UI JSON. The host renders ExtractionConfirm from gap_flag.
7. On a confirm turn, call inventory_confirm with the analyst's quantity and unit.

Rules:
- ALWAYS call tools and persist a draft before stopping.
- Persist only activities present in this run's evidence. Do not invent lines.
- Never chat a list of questions. Collaboration is A2UI only (host-owned).
- Material = unit/OCR conflict that moves company total by more than 5%.
- If extract JSON is source=unavailable, assemble from tabular evidence only.
- If an override exists for {activity_key}_unit, apply it and do not set gap_flag.
- GHG Protocol scopes 1–3 (categories 1–15 as evidenced). Partial inventories are OK.
- Model is Gemini 3.7 Flash via Vertex. Do not switch to Pro.
"""


def mcp_endpoint() -> str:
    raw = os.environ.get("MCP_URL") or "http://127.0.0.1:8081"
    url = raw.rstrip("/")
    return url if url.endswith("/mcp") else f"{url}/mcp"


def mcp_toolset():
    """Return MCPToolset, or None if the ADK MCP client cannot be constructed."""
    endpoint = mcp_endpoint()
    try:
        from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
        from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams

        return MCPToolset(connection_params=StreamableHTTPConnectionParams(url=endpoint))
    except Exception:
        try:
            from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset

            return MCPToolset(connection_params={"url": endpoint})
        except Exception:
            return None


def in_process_tools():
    from tools.erp import get_erp_activity, summarize_erp
    from tools.factors import lookup_factor
    from tools.inventory import apply_extraction_confirm, persist_draft_tool, persist_line_tool
    from tools.memory import load_company_overrides, save_company_override

    print("[greenchain] MCPToolset unavailable; using in-process primitive tools (not run_audit).")
    return [
        load_company_overrides,
        save_company_override,
        get_erp_activity,
        summarize_erp,
        lookup_factor,
        persist_line_tool,
        persist_draft_tool,
        apply_extraction_confirm,
    ]


try:
    from google.adk.agents import Agent

    _mcp_tools = mcp_toolset()
    root_agent = Agent(
        name="audit_lead",
        model=model_id(),
        description="Drafts a GHG inventory from mixed evidence, then asks only at material gaps.",
        instruction=INSTRUCTION.strip(),
        tools=[_mcp_tools] if _mcp_tools is not None else in_process_tools(),
    )
except Exception as exc:  # noqa: BLE001 — local file-mode still runs without ADK/Vertex
    root_agent = None
    ADK_IMPORT_ERROR = str(exc)
else:
    ADK_IMPORT_ERROR = None
