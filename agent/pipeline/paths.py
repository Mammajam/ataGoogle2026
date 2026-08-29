"""Resolve fixture and local-data paths (Windows-safe)."""

from __future__ import annotations

import os
from pathlib import Path

AGENT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = AGENT_ROOT.parent


def fixtures_dir() -> Path:
    return Path(os.environ.get("GREENCHAIN_FIXTURES") or (REPO_ROOT / "fixtures"))


def data_dir() -> Path:
    return Path(os.environ.get("GREENCHAIN_DATA") or (AGENT_ROOT / "data"))


def ensure_data_dirs() -> None:
    root = data_dir()
    for name in ("drafts", "overrides", "evidence", "artifacts", "sessions", "companies"):
        (root / name).mkdir(parents=True, exist_ok=True)


FIXTURES = fixtures_dir()
DATA_DIR = data_dir()
