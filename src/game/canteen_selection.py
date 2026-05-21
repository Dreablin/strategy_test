"""Pick a reachable dining building with a free diner slot and reserve it for a hungry worker."""

from __future__ import annotations

from typing import Any

from game.buildings.registry import BuildingRegistry
from game.canteen_dining import (
    available_meals_for_reservation,
    count_reserved_diner_slots,
    try_reserve_diner_slot_and_meal,
)
from game.config import HUNGER_SATIETY_THRESHOLD
from game.pathfinding import find_path_bfs
from game.worker_models import Worker
from game.worker_tiers import worker_tier
from game.world import World
from game.workers import WorkerManager

_DINING_BUILDING_TYPES: frozenset[str] = frozenset({"CANTEEN", "RESTAURANT"})


def _is_dining_building(building: Any) -> bool:
    return getattr(building, "type_tag", None) in _DINING_BUILDING_TYPES


def _worker_inside_building_footprint(worker: Worker, building: Any) -> bool:
    pos = building.grid_pos
    if pos is None:
        return False
    gx, gy = pos
    w, h = type(building).footprint
    wx, wy = worker.current_tile
    return gx <= wx < gx + w and gy <= wy < gy + h


def _shortest_path_length_to_building(
    world: World,
    worker_manager: WorkerManager,
    worker: Worker,
    building: Any,
    blocked: set[tuple[int, int]],
) -> int | None:
    start = worker.current_tile
    if worker.assigned_building is building and _worker_inside_building_footprint(worker, building):
        return 0
    best: int | None = None
    for tile in worker_manager._approach_tiles(building):
        path = find_path_bfs(world, start, tile, blocked)
        if path is None:
            continue
        plen = len(path)
        if best is None or plen < best:
            best = plen
    return best


def reserve_nearest_reachable_canteen_if_hungry(
    world: World,
    registry: BuildingRegistry,
    worker_manager: WorkerManager,
    worker: Worker,
) -> Any | None:
    """If satiety is below the hunger threshold, reserve the nearest reachable dining building with a free slot."""
    if int(worker.satiety) >= HUNGER_SATIETY_THRESHOLD:
        return None
    if worker.dining_canteen is not None:
        return None

    blocked = world.blocked_tiles()
    blocked.discard(worker.current_tile)

    w_tier = worker_tier(worker.type_tag)
    candidates: list[tuple[int, int, int, Any]] = []
    for building in registry.all():
        if not _is_dining_building(building):
            continue
        if building.is_under_construction:
            continue
        if hasattr(building, "dining_tier") and building.dining_tier() != w_tier:
            continue
        if count_reserved_diner_slots(building) >= building.diner_slot_capacity():
            continue
        if available_meals_for_reservation(building) <= 0:
            continue
        dist = _shortest_path_length_to_building(world, worker_manager, worker, building, blocked)
        if dist is None:
            continue
        pos = building.grid_pos
        gx, gy = pos if pos is not None else (10**9, 10**9)
        candidates.append((dist, gx, gy, building))

    if not candidates:
        return None

    candidates.sort(key=lambda t: (t[0], t[1], t[2], id(t[3])))
    _, _, _, chosen = candidates[0]
    if try_reserve_diner_slot_and_meal(chosen, worker):
        return chosen
    return None
