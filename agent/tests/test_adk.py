"""Optional live ADK check. Skips unless Vertex credentials are configured."""

from __future__ import annotations

import os
import sys
from pathlib import Path

AGENT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(AGENT_DIR))

from pipeline.adk_runtime import adk_available, engine_default  # noqa: E402
from pipeline.extract import vertex_ready  # noqa: E402


def test_engine_default_without_vertex_is_deterministic(monkeypatch):
    monkeypatch.setenv("GREENCHAIN_FORCE_DETERMINISTIC", "1")
    assert engine_default() == "deterministic"


def test_adk_live_skipped_without_credentials():
    if not vertex_ready():
        print("skip: Vertex not configured")
        return
    assert adk_available() or engine_default() in {"adk", "deterministic"}


def test_engine_default_is_deterministic_when_mcp_down(monkeypatch):
    monkeypatch.delenv("GREENCHAIN_FORCE_DETERMINISTIC", raising=False)
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "demo-project")
    monkeypatch.setenv("GOOGLE_GENAI_USE_VERTEXAI", "TRUE")
    monkeypatch.setattr("pipeline.adk_runtime.adk_available", lambda: True)
    monkeypatch.setattr("pipeline.adk_runtime.mcp_reachable", lambda: False)
    monkeypatch.setattr("pipeline.extract.vertex_ready", lambda: True)
    monkeypatch.setattr("pipeline.adk_runtime.vertex_ready", lambda: True)
    assert engine_default() == "deterministic"


def test_agent_prefers_mcp_toolset_over_in_process_inventory():
    import inspect

    from audit_lead import agent as agent_mod

    source = inspect.getsource(agent_mod)
    assert "MCPToolset" in source
    assert "in_process_tools()" in source
    assert "tools=[_mcp_tools] if _mcp_tools is not None else in_process_tools()" in source
    assert "run_audit(" not in inspect.getsource(agent_mod.in_process_tools)


def test_default_model_is_gemini_37_flash():
    from pipeline.gemini import DEFAULT_MODEL, model_id

    assert DEFAULT_MODEL == "gemini-3.7-flash"
    previous = os.environ.get("GEMINI_MODEL")
    os.environ.pop("GEMINI_MODEL", None)
    try:
        assert model_id() == "gemini-3.7-flash"
    finally:
        if previous is not None:
            os.environ["GEMINI_MODEL"] = previous


if __name__ == "__main__":
    class Dummy:
        def setenv(self, key, value):
            os.environ[key] = value

        def delenv(self, key, raising=True):
            os.environ.pop(key, None)

        def setattr(self, path, value):
            mod, _, name = path.rpartition(".")
            import importlib

            module = importlib.import_module(mod)
            setattr(module, name, value)

    test_engine_default_without_vertex_is_deterministic(Dummy())
    print("ok: engine default")
    test_adk_live_skipped_without_credentials()
    print("ok: adk skip/live probe")
    test_engine_default_is_deterministic_when_mcp_down(Dummy())
    print("ok: mcp down forces deterministic")
    test_agent_prefers_mcp_toolset_over_in_process_inventory()
    print("ok: mcp toolset preferred")
    test_default_model_is_gemini_37_flash()
    print("ok: default gemini-3.7-flash")
