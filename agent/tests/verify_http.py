"""Hit the local agent: first run has a widget, confirm kWh, second run is silent."""

from __future__ import annotations

import json
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8080"


def get(path: str) -> dict:
    with urllib.request.urlopen(BASE + path) as res:
        return json.loads(res.read().decode())


def post_json(path: str, payload: dict) -> dict:
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        BASE + path, data=data, headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(req) as res:
        return json.loads(res.read().decode())


def post_run() -> dict:
    boundary = "----greenchain"
    body = (
        f"--{boundary}\r\n"
        'Content-Disposition: form-data; name="company_id"\r\n\r\n'
        "northwind-energy\r\n"
        f"--{boundary}--\r\n"
    ).encode()
    req = urllib.request.Request(
        BASE + "/api/audit/run",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    with urllib.request.urlopen(req) as res:
        return json.loads(res.read().decode())


def main() -> None:
    health = get("/health")
    assert health["ok"] is True, health
    print("health", health["store"], health["model"])

    first = post_run()
    scopes = {int(line["scope"]) for line in first["lines"]}
    assert scopes == {1, 2, 3}, scopes
    assert first["widget"] and first["widget"]["kind"] == "ExtractionConfirm", first.get("widget")
    elec = next(line for line in first["lines"] if line["id"] == "s2-grid-electricity")
    assert elec["unit"] == "MWh", elec
    print("run1", first["run_id"], "widget", first["widget"]["kind"], "total", first["totals"]["total_tco2e"])

    confirmed = post_json(
        "/api/audit/confirm",
        {
            "run_id": first["run_id"],
            "line_id": "s2-grid-electricity",
            "quantity": 184200,
            "unit": "kWh",
        },
    )
    elec2 = next(line for line in confirmed["lines"] if line["id"] == "s2-grid-electricity")
    assert elec2["unit"] == "kWh", elec2
    print("confirm", elec2["tco2e"], "total", confirmed["totals"]["total_tco2e"])

    second = post_run()
    assert second["widget"] is None, second.get("widget")
    assert second["policy_applied"] is True, second
    elec3 = next(line for line in second["lines"] if line["id"] == "s2-grid-electricity")
    assert elec3["unit"] == "kWh", elec3
    print("run2 silent", "policy", second["policy_keys"], "unit", elec3["unit"])
    print("OK")


if __name__ == "__main__":
    try:
        main()
    except urllib.error.HTTPError as exc:
        print(exc.read().decode())
        raise
