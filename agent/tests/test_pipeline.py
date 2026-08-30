"""Focused checks: evidence-assembled close, two sample packs, no demo injection."""

from __future__ import annotations

import inspect
import json
import sys
import uuid
from pathlib import Path

AGENT_DIR = Path(__file__).resolve().parents[1]
REPO = AGENT_DIR.parent
sys.path.insert(0, str(AGENT_DIR))

from pipeline.audit import confirm_extraction, run_audit  # noqa: E402
from pipeline.extract import extract_artifacts  # noqa: E402
from pipeline.paths import fixtures_dir  # noqa: E402
from pipeline.store import get_store  # noqa: E402
from tools import erp as erp_tools  # noqa: E402
from tools import inventory as inventory_tools  # noqa: E402

SAMPLES = REPO / "fixtures" / "samples"


def _reset(tmp_path, monkeypatch):
    monkeypatch.setenv("GREENCHAIN_DATA", str(tmp_path))
    monkeypatch.setenv("GREENCHAIN_STORE", "file")
    monkeypatch.setenv("GREENCHAIN_FORCE_DETERMINISTIC", "1")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-3.7-flash")
    monkeypatch.delenv("CLIMATIQ_API_KEY", raising=False)
    monkeypatch.delenv("GREENCHAIN_FACTOR_URL", raising=False)
    monkeypatch.delenv("GREENCHAIN_ERP_URL", raising=False)
    from pipeline import store as store_mod

    store_mod.reset_store_for_tests()


def _seed(run_id: str, files: dict[str, bytes]) -> None:
    store = get_store()
    for name, data in files.items():
        store.write_artifact(run_id, name, data)


def _northwind_csv() -> dict[str, bytes]:
    path = SAMPLES / "northwind" / "erp_export.csv"
    return {"erp_export.csv": path.read_bytes()}


def _harbor_csv() -> dict[str, bytes]:
    path = SAMPLES / "harbor-logistics" / "erp_export.csv"
    return {"activity.csv": path.read_bytes()}


def _dual_electricity_extract() -> dict:
    return {
        "source": "vertex",
        "confidence": 0.82,
        "readings": [
            {"activity_hint": "electricity", "quantity": 184200, "unit": "kWh", "source_filename": "bill.pdf"},
            {"activity_hint": "electricity", "quantity": 184200, "unit": "MWh", "source_filename": "bill.pdf"},
        ],
    }


def test_northwind_sample_assembles_from_csv_bytes(tmp_path, monkeypatch):
    _reset(tmp_path, monkeypatch)
    run_id = str(uuid.uuid4())
    files = _northwind_csv()
    _seed(run_id, files)
    draft = run_audit(
        company_id="northwind-energy",
        company_name="Northwind Energy Ltd",
        reporting_year=2025,
        region="UK",
        run_id=run_id,
        filenames=list(files),
        extract={"source": "unavailable", "reason": "test"},
    )
    keys = {line["activity_key"] for line in draft["lines"]}
    assert "diesel" in keys
    diesel = next(line for line in draft["lines"] if line["activity_key"] == "diesel")
    assert diesel["quantity"] > 1000
    assert diesel["source_thumb"].endswith(".csv")
    assert all(line.get("activity") != "invented-northwind-only" for line in draft["lines"])
    # Without vision, blank Scope 2 in this CSV is incomplete — not filled from expected_draft.
    elec = next((line for line in draft["lines"] if line["activity_key"] == "electricity"), None)
    if elec:
        assert elec.get("gap_flag") in {"missing_quantity", "assumed_spend", None}


def test_dual_readings_emit_generic_gate_then_memory(tmp_path, monkeypatch):
    _reset(tmp_path, monkeypatch)
    run_id = str(uuid.uuid4())
    files = _northwind_csv()
    _seed(run_id, files)
    first = run_audit(
        company_id="northwind-energy",
        company_name="Northwind Energy Ltd",
        reporting_year=2025,
        region="UK",
        run_id=run_id,
        filenames=list(files),
        extract=_dual_electricity_extract(),
    )
    elec = next(line for line in first["lines"] if line["activity_key"] == "electricity")
    assert first["widget"]["kind"] == "ExtractionConfirm"
    assert first["a2ui"][0]["createSurface"]["surfaceId"] == "extraction-confirm"
    assert elec["gap_flag"] == "unit_conflict"
    assert elec["unit"] == "MWh"

    updated = confirm_extraction(
        run_id=first["run_id"],
        line_id=elec["id"],
        quantity=184200,
        unit="kWh",
        company_id="northwind-energy",
    )
    elec2 = next(line for line in updated["lines"] if line["activity_key"] == "electricity")
    assert elec2["unit"] == "kWh"
    assert abs(float(elec2["tco2e"]) - 38.142) < 0.05
    assert updated["widget"] is None

    run2 = str(uuid.uuid4())
    _seed(run2, files)
    second = run_audit(
        company_id="northwind-energy",
        company_name="Northwind Energy Ltd",
        reporting_year=2025,
        region="UK",
        run_id=run2,
        filenames=list(files),
        extract=_dual_electricity_extract(),
    )
    assert second["widget"] is None
    assert second["policy_applied"] is True
    elec3 = next(line for line in second["lines"] if line["activity_key"] == "electricity")
    assert elec3["unit"] == "kWh"
    assert elec3["memory_applied"] is True


def test_harbor_pack_is_not_northwind_shaped(tmp_path, monkeypatch):
    _reset(tmp_path, monkeypatch)
    run_id = str(uuid.uuid4())
    files = _harbor_csv()
    _seed(run_id, files)
    draft = run_audit(
        company_id="harbor-logistics",
        company_name="Harbor Logistics",
        reporting_year=2025,
        region="UK",
        run_id=run_id,
        filenames=list(files),
        extract={"source": "unavailable"},
    )
    keys = {line["activity_key"] for line in draft["lines"]}
    assert keys == {"diesel", "electricity", "road_freight"}
    assert draft["company_name"] == "Harbor Logistics"
    freight = next(line for line in draft["lines"] if line["activity_key"] == "road_freight")
    assert freight["scope"] == 3
    assert freight["category"] == 4
    assert freight["quantity"] == 92000
    diesel = next(line for line in draft["lines"] if line["activity_key"] == "diesel")
    assert diesel["quantity"] == 4200
    assert "steel_components" not in keys


def test_erp_without_csv_returns_no_tabular_artifact(tmp_path, monkeypatch):
    _reset(tmp_path, monkeypatch)
    payload = json.loads(erp_tools.get_erp_activity("missing-run", "harbor-logistics"))
    assert payload["error"] == "no_tabular_artifact"


def test_empty_upload_is_http_400(tmp_path, monkeypatch):
    _reset(tmp_path, monkeypatch)
    from fastapi.testclient import TestClient

    import main as main_mod

    client = TestClient(main_mod.app)
    res = client.post("/api/audit/run", data={"company_id": "acme"})
    assert res.status_code == 400
    res2 = client.post("/api/audit/run", files={"files": ("x.csv", b"a,b\n1,2", "text/csv")})
    assert res2.status_code in {400, 422}


def test_health_returns_greenchain_payload(tmp_path, monkeypatch):
    _reset(tmp_path, monkeypatch)
    from fastapi.testclient import TestClient

    import main as main_mod

    client = TestClient(main_mod.app)
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["service"] == "greenchain-audit-lead"
    assert "engine_default" in body
    assert "mcp" in body
    assert body["store"]["backend"]
    assert body["factors"]["provider"] in {"fixture", "climatiq", "http"}
    assert body["erp"]["live"] is False
    assert body["model"] == "gemini-3.7-flash"


def test_climatiq_lookup_uses_live_estimate(tmp_path, monkeypatch):
    _reset(tmp_path, monkeypatch)
    monkeypatch.setenv("CLIMATIQ_API_KEY", "test-key")
    from pipeline.factors_provider import ClimatiqProvider, get_provider

    class FakeResponse:
        def __init__(self, payload):
            self._payload = json.dumps(payload).encode()

        def read(self):
            return self._payload

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    calls = {"n": 0}

    def fake_urlopen(req, timeout=10):
        calls["n"] += 1
        url = getattr(req, "full_url", None) or getattr(req, "get_full_url", lambda: "")()
        if "search" in str(url):
            return FakeResponse(
                {
                    "results": [
                        {
                            "id": "ef-diesel",
                            "activity_id": "fuel_type_diesel-fuel_use_mobile",
                            "source": "Climatiq",
                            "year": 2025,
                            "region": "GB",
                            "data_version": "^21",
                        }
                    ]
                }
            )
        return FakeResponse({"co2e": 2.51, "co2e_unit": "kg", "emission_factor": {"id": "ef-diesel", "year": 2025}})

    monkeypatch.setattr("pipeline.factors_provider._urlopen", fake_urlopen)
    provider = get_provider()
    assert isinstance(provider, ClimatiqProvider)
    row = provider.lookup("diesel", "litre", "UK", 2025)
    assert row["provider"] == "climatiq"
    assert abs(float(row["kgco2e_per_unit"]) - 2.51) < 0.01
    assert calls["n"] >= 2


def test_live_erp_fills_when_csv_missing(tmp_path, monkeypatch):
    _reset(tmp_path, monkeypatch)
    monkeypatch.setenv("GREENCHAIN_ERP_URL", "https://erp.example.test/ghg/activity")
    from pipeline.csv_parse import parse_run_tabular

    monkeypatch.setattr(
        "pipeline.csv_parse.fetch_live_erp",
        lambda company_id, run_id=None: (
            [
                {
                    "activity_name": "diesel",
                    "ghg_scope": 1,
                    "quantity": 50,
                    "unit": "litre",
                    "period_month": "2025-01",
                    "spend_gbp": None,
                    "ghg_category": None,
                }
            ],
            "live_erp",
        ),
    )
    rows, source = parse_run_tabular("no-files", "harbor-logistics")
    assert source == "live_erp"
    assert rows[0]["quantity"] == 50


def test_inventory_primitives_do_not_call_run_audit():
    source = inspect.getsource(inventory_tools)
    assert "run_audit(" not in source
    assert "persist_line" in source
    assert "persist_draft" in source


def test_extract_unavailable_without_vertex(monkeypatch):
    monkeypatch.setenv("GREENCHAIN_FORCE_DETERMINISTIC", "1")
    monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)
    result = extract_artifacts([])
    assert result.source == "unavailable"
    assert result.readings == []


def test_high_confidence_extract_returns_readings(monkeypatch):
    class FakeVision:
        def extract(self, artifacts):
            from pipeline.extract import ExtractResult

            return ExtractResult(
                source="vertex",
                confidence=0.91,
                readings=[
                    {"activity_hint": "electricity", "quantity": 184200, "unit": "kWh"},
                    {"activity_hint": "electricity", "quantity": 184200, "unit": "MWh"},
                ],
            )

    monkeypatch.setattr("pipeline.extract.vertex_ready", lambda: True)
    monkeypatch.setattr("pipeline.extract.VertexVisionExtractor", FakeVision)
    result = extract_artifacts([{"filename": "electricity_bill.pdf", "bytes": b"%PDF"}])
    assert result.source == "vertex"
    assert len(result.readings) >= 2


def test_vision_error_is_unavailable_not_fixture(monkeypatch):
    class Boom:
        def extract(self, artifacts):
            raise TimeoutError("vertex timeout")

    monkeypatch.setattr("pipeline.extract.vertex_ready", lambda: True)
    monkeypatch.setattr("pipeline.extract.VertexVisionExtractor", Boom)
    result = extract_artifacts([{"filename": "bill.pdf", "bytes": b"%PDF"}])
    assert result.source == "unavailable"
    assert "vision_unavailable" in (result.reason or "")


def test_fixture_factor_provider_does_not_invent_lines():
    from pipeline.factors_provider import FixtureProvider

    row = FixtureProvider().lookup("diesel", "litre", "UK", 2025)
    assert row.get("error") is None
    assert row["provider"] == "fixture"
    assert "kgco2e_per_unit" in row
    missing = FixtureProvider().lookup("unobtanium", "furlong", "UK", 2025)
    assert missing["error"] == "factor_not_found"


if __name__ == "__main__":
    class Dummy:
        def setenv(self, key, value):
            import os

            os.environ[key] = value

        def delenv(self, key, raising=True):
            import os

            os.environ.pop(key, None)

        def setattr(self, path, value):
            mod, _, name = path.rpartition(".")
            import importlib

            module = importlib.import_module(mod)
            setattr(module, name, value)

    from tempfile import TemporaryDirectory

    with TemporaryDirectory() as folder:
        test_northwind_sample_assembles_from_csv_bytes(Path(folder), Dummy())
        print("ok: northwind csv")
    with TemporaryDirectory() as folder:
        test_dual_readings_emit_generic_gate_then_memory(Path(folder), Dummy())
        print("ok: gate + memory")
    with TemporaryDirectory() as folder:
        test_harbor_pack_is_not_northwind_shaped(Path(folder), Dummy())
        print("ok: harbor pack")
    with TemporaryDirectory() as folder:
        test_erp_without_csv_returns_no_tabular_artifact(Path(folder), Dummy())
        print("ok: erp missing csv")
    with TemporaryDirectory() as folder:
        test_empty_upload_is_http_400(Path(folder), Dummy())
        print("ok: http 400")
    with TemporaryDirectory() as folder:
        test_health_returns_greenchain_payload(Path(folder), Dummy())
        print("ok: health payload")
    with TemporaryDirectory() as folder:
        test_climatiq_lookup_uses_live_estimate(Path(folder), Dummy())
        print("ok: climatiq live mock")
    with TemporaryDirectory() as folder:
        test_live_erp_fills_when_csv_missing(Path(folder), Dummy())
        print("ok: live erp")
    test_inventory_primitives_do_not_call_run_audit()
    print("ok: primitives")
    test_extract_unavailable_without_vertex(Dummy())
    print("ok: extract unavailable")
    test_high_confidence_extract_returns_readings(Dummy())
    print("ok: extract vertex mock")
    test_vision_error_is_unavailable_not_fixture(Dummy())
    print("ok: extract unavailable on error")
    test_fixture_factor_provider_does_not_invent_lines()
    print("ok: factor catalog")
