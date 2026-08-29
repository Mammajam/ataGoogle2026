"""Firestore store with a JSON-file fallback so local `pnpm dev` still works."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pipeline.paths import data_dir, ensure_data_dirs


def _safe_filename(filename: str) -> str:
    name = Path(filename or "upload.bin").name
    if not name or name in {".", ".."}:
        return "upload.bin"
    return name


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

    def write_artifact(self, run_id: str, filename: str, data: bytes) -> str:
        path = self._path("artifacts", run_id, _safe_filename(filename))
        path.write_bytes(data)
        return str(path)

    def read_artifact(self, run_id: str, filename: str) -> bytes | None:
        path = self._path("artifacts", run_id, _safe_filename(filename))
        if not path.exists() or not path.is_file():
            return None
        return path.read_bytes()

    def list_artifacts(self, run_id: str) -> list[str]:
        folder = data_dir() / "artifacts" / run_id
        if not folder.exists():
            return []
        return sorted(item.name for item in folder.iterdir() if item.is_file())

    list_artifact_names = list_artifacts

    def write_company(self, company_id: str, profile: dict[str, Any]) -> dict[str, Any]:
        payload = {**profile, "company_id": company_id, "updatedAt": _now()}
        self._path("companies", f"{company_id}.json").write_text(
            json.dumps(payload, indent=2), encoding="utf-8"
        )
        return payload

    def read_company(self, company_id: str) -> dict[str, Any] | None:
        path = self._path("companies", f"{company_id}.json")
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def save_session(self, run_id: str, session: dict[str, Any]) -> None:
        self._path("sessions", f"{run_id}.json").write_text(
            json.dumps({**session, "run_id": run_id, "updatedAt": _now()}, indent=2),
            encoding="utf-8",
        )

    def load_session(self, run_id: str) -> dict[str, Any] | None:
        path = self._path("sessions", f"{run_id}.json")
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def ping(self) -> bool:
        ensure_data_dirs()
        return True


def _artifact_bucket_name(project: str) -> str:
    return (os.environ.get("GREENCHAIN_ARTIFACT_BUCKET") or "").strip() or f"{project}.appspot.com"


class GcsArtifactStore:
    """Firebase / GCS object storage for run artifacts. Falls back to local files."""

    def __init__(self, project: str) -> None:
        self._files = FileStore()
        self._bucket = None
        self._error: str | None = None
        try:
            from google.cloud import storage  # type: ignore

            client = storage.Client(project=project)
            name = _artifact_bucket_name(project)
            self._bucket = client.bucket(name)
        except Exception as exc:  # noqa: BLE001
            self._error = str(exc)

    def _blob(self, run_id: str, filename: str):
        if self._bucket is None:
            return None
        return self._bucket.blob(f"artifacts/{run_id}/{_safe_filename(filename)}")

    def write_artifact(self, run_id: str, filename: str, data: bytes) -> str:
        local = self._files.write_artifact(run_id, filename, data)
        blob = self._blob(run_id, filename)
        if blob is None:
            return local
        try:
            blob.upload_from_string(data)
            return f"gs://{self._bucket.name}/{blob.name}"
        except Exception:
            return local

    def read_artifact(self, run_id: str, filename: str) -> bytes | None:
        local = self._files.read_artifact(run_id, filename)
        if local is not None:
            return local
        blob = self._blob(run_id, filename)
        if blob is None:
            return None
        try:
            if not blob.exists():
                return None
            return blob.download_as_bytes()
        except Exception:
            return None

    def list_artifacts(self, run_id: str) -> list[str]:
        names = self._files.list_artifacts(run_id)
        if names or self._bucket is None:
            return names
        try:
            prefix = f"artifacts/{run_id}/"
            blobs = self._bucket.list_blobs(prefix=prefix)
            return sorted(blob.name.split("/")[-1] for blob in blobs if blob.name)
        except Exception:
            return []


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
        self._files = FileStore()
        self._artifacts = GcsArtifactStore(project or "") if project else self._files

    def ping(self) -> bool:
        list(self._db.collection("companies").limit(1).stream())
        return True

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
        company_id = evidence.get("company_id") or "unknown"
        (
            self._db.collection("companies")
            .document(company_id)
            .collection("evidence")
            .document(run_id)
            .set(payload)
        )

    def write_artifact(self, run_id: str, filename: str, data: bytes) -> str:
        return self._artifacts.write_artifact(run_id, filename, data)

    def read_artifact(self, run_id: str, filename: str) -> bytes | None:
        return self._artifacts.read_artifact(run_id, filename)

    def list_artifacts(self, run_id: str) -> list[str]:
        return self._artifacts.list_artifacts(run_id)

    list_artifact_names = list_artifacts

    def write_company(self, company_id: str, profile: dict[str, Any]) -> dict[str, Any]:
        payload = {**profile, "company_id": company_id, "updatedAt": _now()}
        self._db.collection("companies").document(company_id).set(payload)
        self._files.write_company(company_id, profile)
        return payload

    def read_company(self, company_id: str) -> dict[str, Any] | None:
        snap = self._db.collection("companies").document(company_id).get()
        if snap.exists:
            return snap.to_dict()
        return self._files.read_company(company_id)

    def save_session(self, run_id: str, session: dict[str, Any]) -> None:
        payload = {**session, "run_id": run_id, "updatedAt": _now()}
        self._db.collection("adk_sessions").document(run_id).set(payload)
        self._files.save_session(run_id, session)

    def load_session(self, run_id: str) -> dict[str, Any] | None:
        snap = self._db.collection("adk_sessions").document(run_id).get()
        if snap.exists:
            return snap.to_dict()
        return self._files.load_session(run_id)


_STORE: FileStore | FirestoreStore | None = None


def _default_store_mode() -> str:
    explicit = (os.environ.get("GREENCHAIN_STORE") or "").strip().lower()
    if explicit:
        return explicit
    project = os.environ.get("GOOGLE_CLOUD_PROJECT") or ""
    if project and not project.startswith("your-"):
        return "firestore"
    return "file"


def get_store() -> FileStore | FirestoreStore:
    global _STORE
    if _STORE is not None:
        return _STORE
    mode = _default_store_mode()
    if mode in {"firestore", "firebase"}:
        try:
            candidate = FirestoreStore()
            candidate.ping()
            _STORE = candidate
            return _STORE
        except Exception as exc:  # noqa: BLE001
            print(f"[greenchain] Firestore unavailable ({exc}); using file store")
    _STORE = FileStore()
    return _STORE


def store_status() -> dict[str, Any]:
    store = get_store()
    name = type(store).__name__
    mode = _default_store_mode()
    try:
        ping = getattr(store, "ping", None)
        ok = bool(ping()) if callable(ping) else True
        return {"backend": name, "ok": ok, "mode": mode}
    except Exception as exc:  # noqa: BLE001
        return {"backend": name, "ok": False, "mode": mode, "error": str(exc)}


def reset_store_for_tests() -> None:
    global _STORE
    _STORE = None
