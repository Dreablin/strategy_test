"""Dining runtime: walk to slot, wait for meal, eat, release slot, return to work."""

from __future__ import annotations

from typing import Any

from game.buildings.registry import BuildingRegistry
from game.canteen_dining import (
    available_meals_for_reservation,
    release_diner_slot_after_meal,
    release_diner_slots_for_worker,
    release_reserved_meal,
)
from game.pathfinding import find_path_bfs
from game.worker_geometry import building_center_tile
from game.worker_models import Worker
from game.worker_satiety import MAX_WORKER_SATIETY
from game.world import World
from game.workers import WorkerManager

DINING_EAT_DURATION_MS = 20_000


def _footprint_adjacent_tiles(building: Any) -> list[tuple[int, int]]:
    pos = building.grid_pos
    if pos is None:
        return []
    gx, gy = pos
    w, h = type(building).footprint
    raw: list[tuple[int, int]] = []
    for y in range(gy - 1, gy + h + 1):
        for x in range(gx - 1, gx + w + 1):
            inside = gx <= x < gx + w and gy <= y < gy + h
            if inside:
                continue
            raw.append((x, y))
    raw.sort(key=lambda t: (t[1], t[0]))
    return raw


def diner_stand_tile_for(building: Any, worker: Worker) -> tuple[int, int]:
    tiles = _footprint_adjacent_tiles(building)
    if not tiles:
        return (0, 0)
    occupants = sorted(building._diner_occupants, key=id)
    try:
        idx = occupants.index(worker)
    except ValueError:
        idx = 0
    return tiles[idx % len(tiles)]


def _reachable_diner_stand_tile_for(
    building: Any,
    worker: Worker,
    worker_manager: WorkerManager,
) -> tuple[int, int] | None:
    tiles = worker_manager._approach_tiles(building)
    if not tiles:
        return None
    tiles.sort(key=lambda t: (t[1], t[0]))
    occupants = sorted(building._diner_occupants, key=id)
    try:
        idx = occupants.index(worker)
    except ValueError:
        idx = 0
    return tiles[idx % len(tiles)]


def _worker_inside_building_footprint(worker: Worker, building: Any) -> bool:
    pos = building.grid_pos
    if pos is None:
        return False
    gx, gy = pos
    w, h = type(building).footprint
    wx, wy = worker.current_tile
    return gx <= wx < gx + w and gy <= wy < gy + h


def dining_runtime_phase(worker: Worker) -> str:
    return str(worker.dining_phase)


def dining_eating_started_ms(worker: Worker) -> int:
    return int(worker.dining_eating_started_ms)


def assign_diner_meals_for_canteen(building: Any, *, now_ms: int = 0) -> None:
    _ = now_ms
    waiting = [
        w
        for w in building._diner_occupants
        if dining_runtime_phase(w) == "waiting_for_meal"
        and not w.dining_meal_reserved
        and int(w.dining_queue_order) >= 0
    ]
    waiting.sort(key=lambda worker: (int(worker.dining_queue_order), id(worker)))
    meals = available_meals_for_reservation(building)
    for w in waiting[:meals]:
        building._reserved_meal_workers.add(w)
        w.dining_meal_reserved = True


def _mark_waiting_for_meal(worker: Worker, building: Any) -> None:
    worker.dining_phase = "waiting_for_meal"
    worker.state = "waiting_for_meal"
    worker.idle = False
    if worker.dining_queue_order < 0:
        worker.dining_queue_order = int(building._diner_queue_seq)
        building._diner_queue_seq += 1
    worker.path = []
    worker.target_tile = None
    worker.segment_progress = 0.0
    worker.stand_tile = worker.current_tile


def _try_start_eating(worker: Worker, building: Any, now_ms: int) -> bool:
    meal_key = str(building.meal_resource_key())
    if not worker.dining_meal_reserved or building.local_storage_amount(meal_key) < 1:
        return False
    building.take_local_storage(meal_key, 1)
    release_reserved_meal(building, worker)
    worker.dining_eating_started_ms = int(now_ms)
    worker.dining_phase = "eating"
    worker.dining_meal_assigned = False
    worker.state = "eating"
    worker.idle = False
    return True


def _complete_return_to_work(worker: Worker) -> None:
    worker.dining_phase = "none"
    worker.dining_eating_started_ms = 0
    worker.dining_meal_assigned = False
    worker.dining_meal_reserved = False
    worker.dining_target_tile = None
    worker.dining_queue_order = -1
    worker.dining_canteen = None
    worker.path = []
    worker.target_tile = None
    worker.segment_progress = 0.0
    assigned = worker.assigned_building
    if assigned is not None and not assigned.is_under_construction:
        worker.current_tile = building_center_tile(assigned)
        worker.stand_tile = worker.current_tile
        worker.state = "working"
        worker.idle = False
    else:
        worker.state = "idle"
        worker.idle = True


def _start_return_to_work(
    worker: Worker,
    *,
    building: Any,
    world: World,
    worker_manager: WorkerManager,
    now_ms: int,
) -> bool:
    assigned = worker.assigned_building
    if assigned is None or assigned.is_under_construction:
        return False
    if assigned is building and _worker_inside_building_footprint(worker, building):
        _complete_return_to_work(worker)
        return True

    blocked = world.blocked_tiles()
    blocked.discard(worker.current_tile)
    best_path: list[tuple[int, int]] | None = None
    for tile in worker_manager._approach_tiles(assigned):
        path = find_path_bfs(world, worker.current_tile, tile, blocked)
        if path is None:
            continue
        if best_path is None or len(path) < len(best_path):
            best_path = path
    if best_path is None:
        return False
    worker.dining_phase = "returning_to_work"
    worker.dining_target_tile = best_path[-1]
    worker.start_move(best_path, now_ms, move_state="returning")
    return True


def _finish_eating(
    worker: Worker,
    building: Any,
    *,
    world: World,
    worker_manager: WorkerManager,
    now_ms: int,
) -> None:
    worker.satiety = MAX_WORKER_SATIETY
    worker.blocked_cycle_hunger_try_ms = -1
    release_diner_slot_after_meal(building, worker)
    worker.dining_eating_started_ms = 0
    worker.dining_meal_assigned = False
    worker.dining_meal_reserved = False
    worker.dining_queue_order = -1
    worker.path = []
    worker.target_tile = None
    worker.segment_progress = 0.0
    worker.dining_canteen = building
    if _start_return_to_work(worker, building=building, world=world, worker_manager=worker_manager, now_ms=now_ms):
        return
    worker.dining_canteen = None
    worker.dining_phase = "none"
    worker.dining_target_tile = None
    assigned = worker.assigned_building
    if assigned is not None and not assigned.is_under_construction:
        worker.state = "working"
        worker.idle = False
        return
    else:
        worker.state = "idle"
        worker.idle = True


def update_dining_runtime(
    worker: Worker,
    *,
    canteen: Any,
    world: World,
    worker_manager: WorkerManager,
    registry: BuildingRegistry,
    now_ms: int,
) -> None:
    _ = (worker_manager, registry)
    building = canteen
    if worker.dining_canteen is not building:
        return
    now_ms = int(now_ms)
    phase = worker.dining_phase

    if phase == "eating":
        worker.state = "eating"
        worker.idle = False
        if now_ms >= worker.dining_eating_started_ms + DINING_EAT_DURATION_MS:
            _finish_eating(worker, building, world=world, worker_manager=worker_manager, now_ms=now_ms)
        return

    if phase == "returning_to_work":
        worker.update(now_ms)
        target = worker.dining_target_tile
        if target is not None and worker.current_tile == target:
            _complete_return_to_work(worker)
        return

    if phase == "waiting_for_meal":
        worker.state = "waiting_for_meal"
        worker.idle = False
        _try_start_eating(worker, building, now_ms)
        return

    if phase == "walking_to_diner":
        worker.update(now_ms)
        target = worker.dining_target_tile
        if target is not None and worker.current_tile == target:
            _mark_waiting_for_meal(worker, building)
        return

    if phase == "none":
        if worker.assigned_building is building and _worker_inside_building_footprint(worker, building):
            worker.dining_target_tile = worker.current_tile
            _mark_waiting_for_meal(worker, building)
            _try_start_eating(worker, building, now_ms)
            return
        target = _reachable_diner_stand_tile_for(building, worker, worker_manager)
        if target is None:
            release_diner_slots_for_worker(worker)
            return
        worker.dining_target_tile = target
        blocked = world.blocked_tiles()
        blocked.discard(worker.current_tile)
        path = find_path_bfs(world, worker.current_tile, target, blocked)
        if path is None:
            worker.dining_target_tile = None
            release_diner_slots_for_worker(worker)
            return
        worker.dining_phase = "walking_to_diner"
        worker.start_move(path, now_ms, move_state="going_to_canteen")
        return
