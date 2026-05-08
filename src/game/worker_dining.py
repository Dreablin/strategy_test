"""Canteen dining: walk to slot, wait for meal, eat, release slot (independent of carriers/processors)."""

from __future__ import annotations

from game.buildings.canteen import Canteen
from game.buildings.registry import BuildingRegistry
from game.canteen_dining import release_diner_slot_after_meal
from game.pathfinding import find_path_bfs
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


def dining_runtime_phase(worker: Worker) -> str:
    return str(worker.dining_phase)


def dining_eating_started_ms(worker: Worker) -> int:
    return int(worker.dining_eating_started_ms)


def assign_diner_meals_for_canteen(canteen: Canteen, *, now_ms: int = 0) -> None:
    _ = now_ms
    waiting = [
        w
        for w in canteen._diner_occupants
        if dining_runtime_phase(w) == "waiting_for_meal" and not w.dining_meal_assigned
    ]
    waiting.sort(key=id)
    meals = canteen.local_storage_amount("simple_meal")
    for w in waiting[:meals]:
        w.dining_meal_assigned = True


def _finish_eating(worker: Worker, canteen: Canteen) -> None:
    worker.satiety = MAX_WORKER_SATIETY
    release_diner_slot_after_meal(canteen, worker)
    worker.dining_phase = "none"
    worker.dining_eating_started_ms = 0
    worker.dining_meal_assigned = False
    worker.dining_target_tile = None
    worker.state = "idle"
    worker.idle = True
    worker.path = []
    worker.target_tile = None
    worker.segment_progress = 0.0


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
        if now_ms >= worker.dining_eating_started_ms + DINING_EAT_DURATION_MS:
            _finish_eating(worker, canteen)
        return

    if phase == "waiting_for_meal":
        if worker.dining_meal_assigned and canteen.local_storage_amount("simple_meal") >= 1:
            canteen.take_local_storage("simple_meal", 1)
            worker.dining_eating_started_ms = now_ms
            worker.dining_phase = "eating"
            worker.dining_meal_assigned = False
        return

    if phase == "walking_to_diner":
        worker.update(now_ms)
        target = worker.dining_target_tile
        if target is not None and worker.current_tile == target:
            worker.dining_phase = "waiting_for_meal"
            worker.state = "idle"
            worker.idle = True
            worker.path = []
            worker.target_tile = None
            worker.segment_progress = 0.0
            worker.stand_tile = worker.current_tile
        return

    if phase == "none":
        target = diner_stand_tile_for(canteen, worker)
        worker.dining_target_tile = target
        blocked = world.blocked_tiles()
        blocked.discard(worker.current_tile)
        path = find_path_bfs(world, worker.current_tile, target, blocked)
        if path is None:
            return
        worker.dining_phase = "walking_to_diner"
        worker.start_move(path, now_ms, move_state="moving")
        return
