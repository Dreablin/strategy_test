"""Canteen dining: walk to slot, wait for meal, eat, release slot (independent of carriers/processors)."""

from __future__ import annotations

from game.buildings.canteen import Canteen
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


def _footprint_adjacent_tiles(canteen: Canteen) -> list[tuple[int, int]]:
    pos = canteen.grid_pos
    if pos is None:
        return []
    gx, gy = pos
    w, h = type(canteen).footprint
    raw: list[tuple[int, int]] = []
    for y in range(gy - 1, gy + h + 1):
        for x in range(gx - 1, gx + w + 1):
            inside = gx <= x < gx + w and gy <= y < gy + h
            if inside:
                continue
            raw.append((x, y))
    raw.sort(key=lambda t: (t[1], t[0]))
    return raw


def diner_stand_tile_for(canteen: Canteen, worker: Worker) -> tuple[int, int]:
    tiles = _footprint_adjacent_tiles(canteen)
    if not tiles:
        return (0, 0)
    occupants = sorted(canteen._diner_occupants, key=id)
    try:
        idx = occupants.index(worker)
    except ValueError:
        idx = 0
    return tiles[idx % len(tiles)]


def _reachable_diner_stand_tile_for(
    canteen: Canteen,
    worker: Worker,
    worker_manager: WorkerManager,
) -> tuple[int, int] | None:
    tiles = worker_manager._approach_tiles(canteen)
    if not tiles:
        return None
    tiles.sort(key=lambda t: (t[1], t[0]))
    occupants = sorted(canteen._diner_occupants, key=id)
    try:
        idx = occupants.index(worker)
    except ValueError:
        idx = 0
    return tiles[idx % len(tiles)]


def _worker_inside_canteen_footprint(worker: Worker, canteen: Canteen) -> bool:
    pos = canteen.grid_pos
    if pos is None:
        return False
    gx, gy = pos
    w, h = type(canteen).footprint
    wx, wy = worker.current_tile
    return gx <= wx < gx + w and gy <= wy < gy + h


def dining_runtime_phase(worker: Worker) -> str:
    return str(worker.dining_phase)


def dining_eating_started_ms(worker: Worker) -> int:
    return int(worker.dining_eating_started_ms)


def assign_diner_meals_for_canteen(canteen: Canteen, *, now_ms: int = 0) -> None:
    _ = now_ms
    waiting = [
        w
        for w in canteen._diner_occupants
        if dining_runtime_phase(w) == "waiting_for_meal"
        and not w.dining_meal_reserved
        and int(w.dining_queue_order) >= 0
    ]
    waiting.sort(key=lambda worker: (int(worker.dining_queue_order), id(worker)))
    meals = available_meals_for_reservation(canteen)
    for w in waiting[:meals]:
        canteen._reserved_meal_workers.add(w)
        w.dining_meal_reserved = True


def _mark_waiting_for_meal(worker: Worker, canteen: Canteen) -> None:
    worker.dining_phase = "waiting_for_meal"
    worker.state = "waiting_for_meal"
    worker.idle = False
    if worker.dining_queue_order < 0:
        worker.dining_queue_order = int(canteen._diner_queue_seq)
        canteen._diner_queue_seq += 1
    worker.path = []
    worker.target_tile = None
    worker.segment_progress = 0.0
    worker.stand_tile = worker.current_tile


def _try_start_eating(worker: Worker, canteen: Canteen, now_ms: int) -> bool:
    if not worker.dining_meal_reserved or canteen.local_storage_amount("simple_meal") < 1:
        return False
    canteen.take_local_storage("simple_meal", 1)
    release_reserved_meal(canteen, worker)
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
    canteen: Canteen,
    world: World,
    worker_manager: WorkerManager,
    now_ms: int,
) -> bool:
    assigned = worker.assigned_building
    if assigned is None or assigned.is_under_construction:
        return False
    if assigned is canteen and _worker_inside_canteen_footprint(worker, canteen):
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
    canteen: Canteen,
    *,
    world: World,
    worker_manager: WorkerManager,
    now_ms: int,
) -> None:
    worker.satiety = MAX_WORKER_SATIETY
    worker.blocked_cycle_hunger_try_ms = -1
    release_diner_slot_after_meal(canteen, worker)
    worker.dining_eating_started_ms = 0
    worker.dining_meal_assigned = False
    worker.dining_meal_reserved = False
    worker.dining_queue_order = -1
    worker.path = []
    worker.target_tile = None
    worker.segment_progress = 0.0
    worker.dining_canteen = canteen
    if _start_return_to_work(worker, canteen=canteen, world=world, worker_manager=worker_manager, now_ms=now_ms):
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
    canteen: Canteen,
    world: World,
    worker_manager: WorkerManager,
    registry: BuildingRegistry,
    now_ms: int,
) -> None:
    _ = (worker_manager, registry)
    if worker.dining_canteen is not canteen:
        return
    now_ms = int(now_ms)
    phase = worker.dining_phase

    if phase == "eating":
        worker.state = "eating"
        worker.idle = False
        if now_ms >= worker.dining_eating_started_ms + DINING_EAT_DURATION_MS:
            _finish_eating(worker, canteen, world=world, worker_manager=worker_manager, now_ms=now_ms)
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
        _try_start_eating(worker, canteen, now_ms)
        return

    if phase == "walking_to_diner":
        worker.update(now_ms)
        target = worker.dining_target_tile
        if target is not None and worker.current_tile == target:
            _mark_waiting_for_meal(worker, canteen)
        return

    if phase == "none":
        if worker.assigned_building is canteen and _worker_inside_canteen_footprint(worker, canteen):
            worker.dining_target_tile = worker.current_tile
            _mark_waiting_for_meal(worker, canteen)
            _try_start_eating(worker, canteen, now_ms)
            return
        target = _reachable_diner_stand_tile_for(canteen, worker, worker_manager)
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
