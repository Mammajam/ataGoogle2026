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
    activity: str = "activity",
    source: str = "evidence",
) -> list[dict[str, Any]]:
    rec_label = (
        f"Confirm {recommended['quantity']:,.0f} {recommended['unit']}  →  {rec_tco2e:,.3f} tCO2e"
    )
    alt_label = (
        f"Use {alternate['quantity']:,.0f} {alternate['unit']}  →  {alt_tco2e:,.3f} tCO2e"
    )
    rec_unit = str(recommended.get("unit") or "rec")
    alt_unit = str(alternate.get("unit") or "alt")
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
                        "children": ["title", "explain", "confidence", "actions"],
                    },
                    {
                        "id": "title",
                        "component": "Text",
                        "text": f"Extraction confirm — {activity}",
                        "variant": "h2",
                    },
                    {"id": "explain", "component": "Text", "text": {"path": "/explanation"}},
                    {"id": "confidence", "component": "Text", "text": {"path": "/confidence_label"}},
                    {"id": "actions", "component": "Column", "children": ["btn-rec", "btn-alt"]},
                    {
                        "id": "btn-rec",
                        "component": "Button",
                        "child": "lbl-rec",
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
                    {"id": "lbl-rec", "component": "Text", "text": rec_label},
                    {
                        "id": "btn-alt",
                        "component": "Button",
                        "child": "lbl-alt",
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
                    {"id": "lbl-alt", "component": "Text", "text": alt_label},
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
                        f"Two readings for {activity} ({rec_unit} vs {alt_unit}) would move "
                        "company tCO2e by more than 5%. Confirm the unit to keep the close."
                    ),
                    "confidence_label": f"Extract confidence {confidence:.0%} on {source}",
                    "line_id": line_id,
                    "run_id": run_id,
                },
            },
        },
    ]
