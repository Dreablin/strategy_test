"""Resource keys: Town Hall warehouse scope vs local-only (e.g. canteen ``simple_meal``)."""

from __future__ import annotations

TOWN_HALL_WAREHOUSE_KEYS: frozenset[str] = frozenset(
    ("wood", "stone", "iron", "wheat", "boards", "flour", "bread", "chicken")
)

SIMPLE_MEAL_KEY = "simple_meal"

_DISPLAY_LABEL_OVERRIDES: dict[str, str] = {
    SIMPLE_MEAL_KEY: "Simple meal",
}


def is_town_hall_warehouse_resource(resource: str) -> bool:
    return str(resource).lower() in TOWN_HALL_WAREHOUSE_KEYS


def is_simple_meal_resource(resource: str) -> bool:
    return str(resource).lower() == SIMPLE_MEAL_KEY


def resource_display_label(resource: str) -> str:
    key = str(resource).lower()
    if key in _DISPLAY_LABEL_OVERRIDES:
        return _DISPLAY_LABEL_OVERRIDES[key]
    return key.replace("_", " ").title()
