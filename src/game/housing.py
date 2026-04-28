"""Housing-domain helpers for population cap calculations."""

from __future__ import annotations

from typing import Any


def housing_town_hall(level: int) -> int:
    lvl = max(1, int(level))
    return 8 + 2 * (lvl - 1)


def housing_house(level: int) -> int:
    lvl = max(1, int(level))
    return 2 + 2 * (lvl - 1)


def max_population(registry: Any, worker_manager_or_count: Any) -> int:
    _ = worker_manager_or_count
    total = 0
    for building in registry.all():
        if building.type_tag == "TOWN_HALL":
            total += housing_town_hall(building.level)
            continue
        if building.type_tag == "HOUSE":
            total += housing_house(building.level)
    return total
