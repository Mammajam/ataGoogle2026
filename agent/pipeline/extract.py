"""Conditional vision extract. Never injects sample-pack quantities."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Protocol

from pipeline.gemini import model_id

CONFIDENCE_FLOOR = 0.75


@dataclass
class ExtractResult:
    source: str  # "vertex" | "unavailable"
    confidence: float
    readings: list[dict[str, Any]] = field(default_factory=list)
    reason: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "confidence": self.confidence,
            "readings": self.readings,
            "reason": self.reason,
            "raw": self.raw,
        }


class Extractor(Protocol):
    def extract(self, artifacts: list[dict[str, Any]]) -> ExtractResult: ...


def unavailable_extract(reason: str = "unavailable") -> ExtractResult:
    return ExtractResult(
        source="unavailable",
        confidence=0.0,
        readings=[],
        reason=reason,
        raw={},
    )


def _readings_from_payload(payload: dict[str, Any]) -> list[dict[str, Any]]:
    readings = list(payload.get("readings") or [])
    if readings:
        return readings
    candidates = list(payload.get("electricity_candidates") or [])
    if not candidates:
        diesel = payload.get("diesel")
        out = []
        if diesel:
            out.append(
                {
                    "activity_hint": "diesel",
                    "quantity": diesel.get("quantity"),
                    "unit": diesel.get("unit") or "litre",
                    "confidence": payload.get("confidence"),
                    "source_filename": diesel.get("source") or "",
                }
            )
        return out
    kwh = next((item for item in candidates if str(item.get("unit", "")).lower() == "kwh"), None)
    mwh = next((item for item in candidates if str(item.get("unit", "")).lower() == "mwh"), None)
    primary = kwh or candidates[0]
    reading = {
        "activity_hint": "electricity",
        "quantity": primary.get("quantity"),
        "unit": primary.get("unit"),
        "confidence": payload.get("confidence"),
        "source_filename": payload.get("source_filename") or "",
    }
    if kwh and mwh:
        reading["alternate_quantity"] = mwh.get("quantity")
        reading["alternate_unit"] = mwh.get("unit")
    return [reading]


class VertexVisionExtractor:
    """Gemini multimodal extract. Raises on transport/parse failure."""

    def extract(self, artifacts: list[dict[str, Any]]) -> ExtractResult:
        from google import genai
        from google.genai import types

        project = os.environ.get("GOOGLE_CLOUD_PROJECT") or ""
        location = os.environ.get("GOOGLE_CLOUD_LOCATION") or "us-central1"
        model = model_id()
        client = genai.Client(vertexai=True, project=project, location=location)

        parts: list[Any] = [
            types.Part.from_text(
                text=(
                    "Extract GHG activity quantities from these files. Return JSON only: "
                    '{"confidence": 0-1, "readings": [{"activity_hint": string, '
                    '"quantity": number, "unit": string, "alternate_quantity": number|null, '
                    '"alternate_unit": string|null, "source_filename": string, "confidence": 0-1}]}. '
                    "List EVERY printed quantity-unit pair, including equivalent-unit headings."
                )
            )
        ]
        for item in artifacts:
            name = str(item.get("filename") or "")
            data = item.get("bytes") or b""
            lower = name.lower()
            if lower.endswith(".pdf"):
                parts.append(types.Part.from_bytes(data=data, mime_type="application/pdf"))
            elif lower.endswith((".jpg", ".jpeg", ".png", ".webp")):
                mime = (
                    "image/jpeg"
                    if lower.endswith((".jpg", ".jpeg"))
                    else f"image/{lower.rsplit('.', 1)[-1]}"
                )
                parts.append(types.Part.from_bytes(data=data, mime_type=mime))

        response = client.models.generate_content(
            model=model,
            contents=[types.Content(role="user", parts=parts)],
            config=types.GenerateContentConfig(response_mime_type="application/json"),
        )
        text = (response.text or "").strip()
        payload = json.loads(text)
        confidence = float(payload.get("confidence") or 0)
        readings = _readings_from_payload(payload)
        if confidence < CONFIDENCE_FLOOR or not readings:
            raise ValueError(f"low_confidence:{confidence}")
        return ExtractResult(
            source="vertex",
            confidence=confidence,
            readings=readings,
            raw=payload,
        )


def vertex_ready() -> bool:
    force = (os.environ.get("GREENCHAIN_FORCE_DETERMINISTIC") or "").lower()
    if force in {"1", "true", "yes"}:
        return False
    project = os.environ.get("GOOGLE_CLOUD_PROJECT") or ""
    if not project or project.startswith("your-"):
        return False
    flag = (os.environ.get("GOOGLE_GENAI_USE_VERTEXAI") or "").lower()
    return flag in {"1", "true", "yes"}


def extract_artifacts(artifacts: list[dict[str, Any]]) -> ExtractResult:
    visual = [
        item
        for item in artifacts
        if str(item.get("filename") or "").lower().endswith((".pdf", ".jpg", ".jpeg", ".png", ".webp"))
    ]
    if not visual:
        return unavailable_extract("no_visual_artifacts")
    if not vertex_ready():
        return unavailable_extract("vertex_unavailable")
    try:
        return VertexVisionExtractor().extract(artifacts)
    except Exception as exc:  # noqa: BLE001
        return unavailable_extract(reason=f"vision_unavailable: {exc}")
