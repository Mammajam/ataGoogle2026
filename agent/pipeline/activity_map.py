"""Map client activity names onto factor catalog keys."""

from __future__ import annotations

import re

SYNONYMS: dict[str, tuple[str, ...]] = {
    "diesel": ("diesel", "gasoil", "gas_oil", "red_diesel", "gas oil", "fleet diesel", "diesel (fleet)"),
    "petrol": ("petrol", "gasoline", "motor_gasoline", "unleaded"),
    "natural_gas": ("natural_gas", "natural gas", "gas", "lng", "methane", "mains gas"),
    "electricity": (
        "electricity",
        "grid",
        "grid_power",
        "grid electricity",
        "kwh",
        "power",
        "electricity_bill",
    ),
    "steel_components": ("steel", "steel_components", "steel components"),
    "industrial_lubricants": ("lubricants", "industrial_lubricants", "industrial lubricants"),
    "electrical_cables": ("cables", "electrical_cables", "electrical cables"),
    "office_supplies": ("office", "office_supplies", "office supplies"),
    "air_travel": ("air_travel", "air travel", "flights", "aviation"),
    "waste": ("waste", "landfill", "refuse"),
    "freight": ("freight", "ocean freight", "logistics", "shipping", "haulage"),
    "road_freight": ("road_freight", "road freight", "hgv", "truck freight"),
    "purchased_goods": ("purchased_goods", "purchased goods", "goods", "materials"),
}


def slugify(name: str) -> str:
    text = (name or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_") or "activity"


def map_activity(raw_name: str, sector: str | None = None) -> str:
    slug = slugify(raw_name)
    compact = slug.replace("_", " ")
    for key, aliases in SYNONYMS.items():
        alias_slugs = {slugify(item) for item in (key, *aliases)}
        alias_compact = {item.lower() for item in aliases}
        if slug in alias_slugs or compact in alias_compact:
            return key
    _ = sector
    return slug
