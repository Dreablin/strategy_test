"""Hiring helpers for worker management."""

from __future__ import annotations

from typing import Any

from game.buildings.base import Building
from game.config import TOWN_HALL_MIN_LEVEL_FOR_HIRE
from game.housing import current_population, max_population
from game.worker_geometry import building_center_tile, town_hall_spawn_tile
from game.worker_models import Worker

WORKER_TO_BUILDING: dict[str, str] = {
    "LUMBERJACK": "LUMBER_CAMP",
    "STONECUTTER": "STONE_MINE",
    "MINER": "IRON_MINE",
    "FARMER": "FARM",
    "ANIMAL_HERDER": "CHICKEN_FARM",
    "FORESTER": "FORESTER_HUT",
    "SAWYER": "SAWMILL",
    "MILLER": "MILL",
    "BAKER": "BAKERY",
}
HIRABLE_WORKERS: set[str] = set(WORKER_TO_BUILDING) | {"CARRIER", "BUILDER", "BAKER", "ANIMAL_HERDER"}


def hire(
    manager: Any,
    worker_type: str,
    *,
    source_building: Building | None = None,
    charge_cost: bool = True,
) -> Worker | None:
    """Hire a worker if town hall level and housing allow it."""
    if manager._registry is None:
        return None
    if worker_type not in manager._HIRABLE_WORKERS:
        return None
    if not has_housing_capacity_for(manager, incoming=1):
        return None
    min_level = int(TOWN_HALL_MIN_LEVEL_FOR_HIRE.get(worker_type, 1))
    th_level = 0
    for b in manager._registry.all():
        if b.type_tag == "TOWN_HALL":
            th_level = b.level
            break
    if th_level < min_level:
        return None
    _ = charge_cost
    spawn_anchor = source_building
    all_buildings = manager._registry.all()
    if spawn_anchor not in all_buildings:
        spawn_anchor = None
    if spawn_anchor is None:
        schools = [b for b in all_buildings if b.type_tag == "SCHOOL"]
        if schools:
            # Hiring is centralized in School; if caller did not pass explicit source,
            # prefer the latest placed school over Town Hall legacy spawn.
            spawn_anchor = schools[-1]
        else:
            spawn_anchor = next((b for b in all_buildings if b.type_tag == "TOWN_HALL"), None)
    stand = (17, 19)
    if spawn_anchor is not None:
        if spawn_anchor.type_tag == "TOWN_HALL":
            stand = town_hall_spawn_tile(spawn_anchor)
        else:
            pos = spawn_anchor.grid_pos
            if pos is None:
                stand = building_center_tile(spawn_anchor)
            else:
                gx, gy = pos
                w, h = type(spawn_anchor).footprint
                # For School hiring, spawn at the tile below the building center.
                stand = (gx + w // 2, gy + h)
        world = getattr(manager._registry, "_world", None)
        if world is not None and (
            not world.is_in_grass(*stand) or world.is_occupied(*stand)
        ):
            approaches = manager._approach_tiles(spawn_anchor)
            if approaches:
                stand = approaches[0]
            else:
                stand = building_center_tile(spawn_anchor)
    worker = Worker(worker_type, stand_tile=stand)
    manager._workers.append(worker)
    return worker


def can_hire(manager: Any, worker_type: str, *, charge_cost: bool = True) -> bool:
    """Whether current state allows hiring this worker type."""
    if manager._registry is None:
        return False
    if worker_type not in manager._HIRABLE_WORKERS:
        return False
    if not has_housing_capacity_for(manager, incoming=1):
        return False
    min_level = int(TOWN_HALL_MIN_LEVEL_FOR_HIRE.get(worker_type, 1))
    th_level = 0
    for b in manager._registry.all():
        if b.type_tag == "TOWN_HALL":
            th_level = b.level
            break
    _ = charge_cost
    return th_level >= min_level


def has_housing_capacity_for(manager: Any, *, incoming: int) -> bool:
    if manager._registry is None:
        return True
    cap = max_population(manager._registry, manager)
    pop_now = current_population(manager._registry, manager)
    return pop_now + int(incoming) <= cap
