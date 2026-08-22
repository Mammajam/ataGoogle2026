"""Focused checks for the demo loop: draft first, planted widget, silent rerun."""

from __future__ import annotations

import json
import sys
from pathlib import Path

AGENT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(AGENT_DIR))

from pipeline.audit import confirm_extraction, run_audit  # noqa: E402
from pipeline.store import get_store  # noqa: E402


def test_first_run_writes_three_scopes_and_widget(tmp_path, monkeypatch):
    monkeypatch.setenv("GREENCHAIN_DATA", str(tmp_path))
    monkeypatch.setenv("GREENCHAIN_STORE", "file")
    from pipeline import store as store_mod

    store_mod.reset_store_for_tests()

    draft = run_audit(company_id="northwind-energy")
    scopes = {int(line["scope"]) for line in draft["lines"]}
    assert scopes == {1, 2, 3}
    assert draft["widget"]["kind"] == "ExtractionConfirm"
    assert draft["a2ui"][0]["createSurface"]["surfaceId"] == "extraction-confirm"
    elec = next(line for line in draft["lines"] if line["id"] == "s2-grid-electricity")
    assert elec["unit"] == "MWh"
    assert elec["gap_flag"] == "unit_conflict"
    assert get_store().read_draft(draft["run_id"]) is not None


def test_confirm_recomputes_kwh_and_second_run_is_silent(tmp_path, monkeypatch):
    monkeypatch.setenv("GREENCHAIN_DATA", str(tmp_path))
    monkeypatch.setenv("GREENCHAIN_STORE", "file")
    from pipeline import store as store_mod

    store_mod.reset_store_for_tests()

    first = run_audit()
    updated = confirm_extraction(
        run_id=first["run_id"],
        line_id="s2-grid-electricity",
        quantity=184200,
        unit="kWh",
    )
    elec = next(line for line in updated["lines"] if line["id"] == "s2-grid-electricity")
    assert elec["unit"] == "kWh"
    assert abs(elec["tco2e"] - 38.142) < 0.02
    assert updated["widget"] is None

    second = run_audit()
    assert second["widget"] is None
    assert second["policy_applied"] is True
    elec2 = next(line for line in second["lines"] if line["id"] == "s2-grid-electricity")
    assert elec2["unit"] == "kWh"
    assert elec2["memory_applied"] is True


if __name__ == "__main__":
    # Tiny runner so verification does not require pytest to be installed.
    class Dummy:
        def setenv(self, key, value):
            import os

            os.environ[key] = value

    from tempfile import TemporaryDirectory

    with TemporaryDirectory() as folder:
        test_first_run_writes_three_scopes_and_widget(Path(folder), Dummy())
        print("ok: first run")
    with TemporaryDirectory() as folder:
        test_confirm_recomputes_kwh_and_second_run_is_silent(Path(folder), Dummy())
        print("ok: memory rerun")
