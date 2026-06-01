"""Resource keys: Town Hall warehouse scope vs local-only (e.g. canteen ``simple_meal``)."""

from __future__ import annotations

from game import i18n

TOWN_HALL_WAREHOUSE_KEYS: frozenset[str] = frozenset(
    (
        "wood",
        "stone",
        "iron",
        "wheat",
        "boards",
        "flour",
        "bread",
        "chicken",
        "beef",
        "hide",
        "grapes",
        "wine",
    )
)

SIMPLE_MEAL_KEY = "simple_meal"
ELITE_MEAL_KEY = "elite_meal"

LOCAL_ONLY_MEAL_KEYS: frozenset[str] = frozenset((SIMPLE_MEAL_KEY, ELITE_MEAL_KEY))


def is_town_hall_warehouse_resource(resource: str) -> bool:
    return str(resource).lower() in TOWN_HALL_WAREHOUSE_KEYS


def is_simple_meal_resource(resource: str) -> bool:
    return str(resource).lower() == SIMPLE_MEAL_KEY


def is_local_only_meal(resource: str) -> bool:
    return str(resource).lower() in LOCAL_ONLY_MEAL_KEYS


def resource_display_label(resource: str) -> str:
    key = str(resource).lower()
    locale_key = f"resource.{key}"
    label = i18n.t(locale_key)
    if label != locale_key:
        return label
    return key.replace("_", " ").title()
