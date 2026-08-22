"""Resolve fixture and local-data paths (Windows-safe)."""

from __future__ import annotations

import os
from pathlib import Path

AGENT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = AGENT_ROOT.parent


def fixtures_dir() -> Path:
    return Path(os.environ.get("GREENCHAIN_FIXTURES", REPO_ROOT / "fixtures"))


def data_dir() -> Path:
    return Path(os.environ.get("GREENCHAIN_DATA", AGENT_ROOT / "data"))


def ensure_data_dirs() -> None:
    root = data_dir()
    (root / "drafts").mkdir(parents=True, exist_ok=True)
    (root / "overrides").mkdir(parents=True, exist_ok=True)
    (root / "evidence").mkdir(parents=True, exist_ok=True)


# Back-compat names used by older imports
FIXTURES = fixtures_dir()
DATA_DIR = data_dir()
