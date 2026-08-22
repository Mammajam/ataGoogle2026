"""Firestore store with a JSON-file fallback so local `npm run dev` still works."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pipeline.paths import data_dir, ensure_data_dirs

COMPANY_ID = os.environ.get("GREENCHAIN_COMPANY_ID", "northwind-energy")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class FileStore:
    """Local stand-in for Firestore collections."""

    def __init__(self) -> None:
        ensure_data_dirs()

    def _path(self, *parts: str) -> Path:
        path = data_dir().joinpath(*parts)
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def write_draft(self, run_id: str, draft: dict[str, Any]) -> dict[str, Any]:
        payload = {**draft, "run_id": run_id, "updatedAt": _now()}
        self._path("drafts", f"{run_id}.json").write_text(
            json.dumps(payload, indent=2), encoding="utf-8"
        )
        return payload

    def read_draft(self, run_id: str) -> dict[str, Any] | None:
        path = self._path("drafts", f"{run_id}.json")
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def list_overrides(self, company_id: str) -> list[dict[str, Any]]:
        folder = data_dir() / "overrides" / company_id
        if not folder.exists():
            return []
        items = []
        for file in sorted(folder.glob("*.json")):
            items.append(json.loads(file.read_text(encoding="utf-8")))
        return items

    def upsert_override(self, company_id: str, override: dict[str, Any]) -> dict[str, Any]:
        key = override["key"]
        payload = {**override, "company_id": company_id, "updatedAt": _now()}
        if "createdAt" not in payload:
            payload["createdAt"] = payload["updatedAt"]
        self._path("overrides", company_id, f"{key}.json").write_text(
            json.dumps(payload, indent=2), encoding="utf-8"
        )
        return payload

    def write_evidence(self, run_id: str, evidence: dict[str, Any]) -> None:
        payload = {**evidence, "run_id": run_id, "updatedAt": _now()}
        self._path("evidence", f"{run_id}.json").write_text(
            json.dumps(payload, indent=2), encoding="utf-8"
        )


class FirestoreStore:
    def __init__(self) -> None:
        from google.cloud import firestore  # type: ignore

        kwargs: dict[str, Any] = {}
        database = os.environ.get("FIRESTORE_DATABASE")
        if database:
            kwargs["database"] = database
        project = os.environ.get("GOOGLE_CLOUD_PROJECT")
        if project:
            kwargs["project"] = project
        self._db = firestore.Client(**kwargs)

    def write_draft(self, run_id: str, draft: dict[str, Any]) -> dict[str, Any]:
        payload = {**draft, "run_id": run_id, "updatedAt": _now()}
        self._db.collection("drafts").document(run_id).set(payload)
        return payload

    def read_draft(self, run_id: str) -> dict[str, Any] | None:
        snap = self._db.collection("drafts").document(run_id).get()
        return snap.to_dict() if snap.exists else None

    def list_overrides(self, company_id: str) -> list[dict[str, Any]]:
        docs = (
            self._db.collection("companies")
            .document(company_id)
            .collection("overrides")
            .stream()
        )
        return [doc.to_dict() | {"id": doc.id} for doc in docs]

    def upsert_override(self, company_id: str, override: dict[str, Any]) -> dict[str, Any]:
        key = override["key"]
        payload = {**override, "company_id": company_id, "updatedAt": _now()}
        if "createdAt" not in payload:
            payload["createdAt"] = payload["updatedAt"]
        (
            self._db.collection("companies")
            .document(company_id)
            .collection("overrides")
            .document(key)
            .set(payload)
        )
        return payload

    def write_evidence(self, run_id: str, evidence: dict[str, Any]) -> None:
        payload = {**evidence, "run_id": run_id, "updatedAt": _now()}
        company_id = evidence.get("company_id", COMPANY_ID)
        (
            self._db.collection("companies")
            .document(company_id)
            .collection("evidence")
            .document(run_id)
            .set(payload)
        )


_STORE: FileStore | FirestoreStore | None = None


def get_store() -> FileStore | FirestoreStore:
    global _STORE
    if _STORE is not None:
        return _STORE
    mode = os.environ.get("GREENCHAIN_STORE", "file").lower()
    if mode == "firestore":
        try:
            _STORE = FirestoreStore()
            return _STORE
        except Exception as exc:  # noqa: BLE001 — local demo must not die on IAM
            print(f"[greenchain] Firestore unavailable ({exc}); using file store")
    _STORE = FileStore()
    return _STORE


def reset_store_for_tests() -> None:
    global _STORE
    _STORE = None
