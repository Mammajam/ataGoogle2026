"""A2UI v0.9 basic-catalog surfaces (Card / Column / Text / Button)."""

from __future__ import annotations

from typing import Any

BASIC_CATALOG_ID = "https://a2ui.org/specification/v0_9/catalogs/basic/catalog.json"
SURFACE_ID = "extraction-confirm"


def extraction_confirm_messages(
    *,
    run_id: str,
    line_id: str,
    recommended: dict[str, Any],
    alternate: dict[str, Any],
    rec_tco2e: float,
    alt_tco2e: float,
    confidence: float,
) -> list[dict[str, Any]]:
    """Compose ExtractionConfirm from the v0.9 basic catalog only (no custom widgets)."""
    rec_label = (
        f"Confirm {recommended['quantity']:,.0f} {recommended['unit']}  →  {rec_tco2e:,.3f} tCO2e"
    )
    alt_label = (
        f"Use {alternate['quantity']:,.0f} {alternate['unit']}  →  {alt_tco2e:,.3f} tCO2e"
    )
    return [
        {
            "version": "v0.9",
            "createSurface": {"surfaceId": SURFACE_ID, "catalogId": BASIC_CATALOG_ID},
        },
        {
            "version": "v0.9",
            "updateComponents": {
                "surfaceId": SURFACE_ID,
                "components": [
                    {"id": "root", "component": "Card", "child": "body"},
                    {
                        "id": "body",
                        "component": "Column",
                        "children": [
                            "title",
                            "explain",
                            "confidence",
                            "actions",
                        ],
                    },
                    {
                        "id": "title",
                        "component": "Text",
                        "text": "Extraction confirm — kWh vs MWh",
                        "variant": "h2",
                    },
                    {
                        "id": "explain",
                        "component": "Text",
                        "text": {
                            "path": "/explanation",
                        },
                    },
                    {
                        "id": "confidence",
                        "component": "Text",
                        "text": {"path": "/confidence_label"},
                    },
                    {
                        "id": "actions",
                        "component": "Column",
                        "children": ["btn-kwh", "btn-mwh"],
                    },
                    {
                        "id": "btn-kwh",
                        "component": "Button",
                        "child": "lbl-kwh",
                        "variant": "primary",
                        "action": {
                            "event": {
                                "name": "extraction.confirm",
                                "context": {
                                    "run_id": run_id,
                                    "line_id": line_id,
                                    "quantity": recommended["quantity"],
                                    "unit": recommended["unit"],
                                    "candidate": "recommended",
                                },
                            }
                        },
                    },
                    {"id": "lbl-kwh", "component": "Text", "text": rec_label},
                    {
                        "id": "btn-mwh",
                        "component": "Button",
                        "child": "lbl-mwh",
                        "variant": "secondary",
                        "action": {
                            "event": {
                                "name": "extraction.confirm",
                                "context": {
                                    "run_id": run_id,
                                    "line_id": line_id,
                                    "quantity": alternate["quantity"],
                                    "unit": alternate["unit"],
                                    "candidate": "alternate",
                                },
                            }
                        },
                    },
                    {"id": "lbl-mwh", "component": "Text", "text": alt_label},
                ],
            },
        },
        {
            "version": "v0.9",
            "updateDataModel": {
                "surfaceId": SURFACE_ID,
                "path": "/",
                "value": {
                    "explanation": (
                        "Vision is 70% sure the Northern Powergrid bill is 184,200 kWh, "
                        "not 184,200 MWh. Confirming the unit is a material judgment "
                        "(it moves company tCO2e by more than 5%)."
                    ),
                    "confidence_label": f"OCR confidence {confidence:.0%} on electricity_bill.pdf",
                    "line_id": line_id,
                    "run_id": run_id,
                },
            },
        },
    ]
