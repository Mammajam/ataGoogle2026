"""Hit the local agent with a real uploaded CSV (no empty-file demo injection)."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path

BASE = "http://127.0.0.1:8080"
SAMPLE = Path(__file__).resolve().parents[2] / "fixtures" / "samples" / "harbor-logistics" / "erp_export.csv"


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
    csv_bytes = SAMPLE.read_bytes()
    boundary = "----greenchain"
    chunks = [
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"company_id\"\r\n\r\nharbor-logistics\r\n".encode(),
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"company_name\"\r\n\r\nHarbor Logistics\r\n".encode(),
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"reporting_year\"\r\n\r\n2025\r\n".encode(),
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"region\"\r\n\r\nUK\r\n".encode(),
        (
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="files"; filename="activity.csv"\r\n'
            "Content-Type: text/csv\r\n\r\n"
        ).encode()
        + csv_bytes
        + b"\r\n",
        f"--{boundary}--\r\n".encode(),
    ]
    body = b"".join(chunks)
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
    store = health.get("store") if isinstance(health.get("store"), dict) else {}
    print(
        "health",
        store.get("backend") or health.get("store"),
        health.get("model"),
        health.get("engine_default"),
        "factors",
        (health.get("factors") or {}).get("provider"),
        "erp_live",
        health.get("erp_live"),
    )

    first = post_run()
    keys = {line["activity_key"] for line in first["lines"]}
    assert "diesel" in keys and "electricity" in keys, keys
    print("run1", first["run_id"], "company", first["company_name"], "lines", keys)
    print("OK")


if __name__ == "__main__":
    try:
        main()
    except urllib.error.HTTPError as exc:
        print(exc.read().decode())
        raise
