"""Classify uploaded artifacts by MIME and content, never by Northwind filenames."""

from __future__ import annotations

from typing import Any


def classify_filename(name: str, data: bytes | None = None, content_type: str | None = None) -> str:
    mime = (content_type or "").split(";")[0].strip().lower()
    if mime in {"text/csv", "application/csv"}:
        return "erp_tabular"
    if mime == "application/pdf":
        return "utility_bill"
    if mime.startswith("image/") and mime.split("/", 1)[-1] in {"jpeg", "jpg", "png", "webp"}:
        return "invoice_receipt"
    lower = (name or "").lower()
    if lower.endswith(".csv"):
        return "erp_tabular"
    if lower.endswith(".pdf"):
        return "utility_bill"
    if lower.endswith((".jpg", ".jpeg", ".png", ".webp")):
        return "invoice_receipt"
    if data:
        if data[:4] == b"%PDF":
            return "utility_bill"
        if data[:3] == b"\xff\xd8\xff" or data[:8] == b"\x89PNG\r\n\x1a\n":
            return "invoice_receipt"
        if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
            return "invoice_receipt"
        if _looks_like_csv(data):
            return "erp_tabular"
    return "unknown"


def _looks_like_csv(data: bytes) -> bool:
    try:
        text = data[:4096].decode("utf-8", errors="ignore")
    except Exception:
        return False
    first = text.splitlines()[0] if text else ""
    return "," in first and any(
        token in first.lower()
        for token in ("scope", "activity", "quantity", "spend", "period")
    )


def classify_uploads(uploads: list[dict[str, Any]]) -> list[dict[str, Any]]:
    items = []
    for item in uploads:
        name = str(item.get("filename") or "upload.bin")
        data = item.get("bytes") or b""
        items.append(
            {
                "filename": name,
                "role": classify_filename(
                    name,
                    data if isinstance(data, bytes) else None,
                    str(item.get("content_type") or "") or None,
                ),
                "bytes": len(data) if isinstance(data, (bytes, bytearray)) else 0,
            }
        )
    return items
