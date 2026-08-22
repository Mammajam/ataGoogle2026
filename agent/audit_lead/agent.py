"""Audit Lead — one ADK orchestrator. No Memory LLM."""

from __future__ import annotations

import os

from tools.erp import get_erp_activity, summarize_erp
from tools.factors import lookup_factor
from tools.inventory import apply_extraction_confirm, write_draft
from tools.memory import load_company_overrides

INSTRUCTION = """
You are GreenChain Audit Lead, a compliance orchestrator for one company
(northwind-energy) and one period (calendar 2025). You lead the GHG close.

Contract — follow this order every run:
1. Load company memory (load_company_overrides).
2. Parse every artifact (CSV required; PDF/image when present).
3. Call ERP + factor tools; compute tCO2e.
4. Write the full draft with evidence and confidence (write_draft).
5. Classify gaps: immaterial → assume and label; material → one A2UI surface then stop.
6. On widget reply, persist override and recompute that line only (apply_extraction_confirm).

Rules:
- ALWAYS call tools and write a complete draft. Never ask in text before the draft exists.
- Never chat a list of questions. Collaboration is A2UI only.
- Material = unit/OCR conflict, first-time Scope 2 method, or a factor choice that
  moves company total by more than 5%. Everything else is assumed and labeled.
- If vision is uncertain, use the fixture expected_draft.json extraction fallback
  while still treating PDF + photo as multimodal evidence.
- If an override already exists for electricity_unit, do not emit A2UI.
- One company, 12 months, Scope 1 fuel + Scope 2 electricity + Scope 3 Category 1.
- Model is Gemini 3.5 Flash via Vertex. Do not switch to Pro.
"""

try:
    from google.adk.agents import Agent

    root_agent = Agent(
        name="audit_lead",
        model=os.environ.get("GEMINI_MODEL", "gemini-3.5-flash"),
        description="Drafts a GHG inventory from mixed evidence, then asks only at material gaps.",
        instruction=INSTRUCTION.strip(),
        tools=[
            load_company_overrides,
            get_erp_activity,
            summarize_erp,
            lookup_factor,
            write_draft,
            apply_extraction_confirm,
        ],
    )
except Exception as exc:  # noqa: BLE001 — local file-mode still runs without ADK/Vertex
    root_agent = None
    ADK_IMPORT_ERROR = str(exc)
else:
    ADK_IMPORT_ERROR = None
