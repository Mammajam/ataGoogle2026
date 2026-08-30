"""Vertex Gemini model id for ADK, vision extract, and health."""

from __future__ import annotations

import os

DEFAULT_MODEL = "gemini-3.7-flash"


def model_id() -> str:
    return os.environ.get("GEMINI_MODEL") or DEFAULT_MODEL


def model_label() -> str:
    mid = model_id()
    if mid == "gemini-3.7-flash":
        return "Gemini 3.7 Flash"
    if mid == "gemini-3.5-flash":
        return "Gemini 3.5 Flash"
    return mid
