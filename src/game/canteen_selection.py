"""Pick a reachable canteen with a free diner slot and reserve it for a hungry worker."""

from __future__ import annotations

from game.buildings.canteen import Canteen
from game.buildings.registry import BuildingRegistry
from game.canteen_dining import count_reserved_diner_slots, try_reserve_diner_slot
from game.pathfinding import find_path_bfs
from game.worker_models import Worker
from game.world import World
from game.workers import WorkerManager

HUNGER_SATIETY_THRESHOLD = 2_000


def _shortest_path_length_to_canteen(
    world: World,
    worker_manager: WorkerManager,
    worker: Worker,
    canteen: Canteen,
    blocked: set[tuple[int, int]],
) -> int | None:
    start = worker.current_tile
    best: int | None = None
    for tile in worker_manager._approach_tiles(canteen):
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
) -> Canteen | None:
    """If satiety is below the hunger threshold, reserve the nearest reachable canteen with a free slot."""
    if int(worker.satiety) >= HUNGER_SATIETY_THRESHOLD:
        return None
    if worker.dining_canteen is not None:
        return None

    blocked = world.blocked_tiles()
    blocked.discard(worker.current_tile)

    candidates: list[tuple[int, int, int, Canteen]] = []
    for building in registry.all():
        if not isinstance(building, Canteen):
            continue
        if building.is_under_construction:
            continue
        if count_reserved_diner_slots(building) >= building.diner_slot_capacity():
            continue
        dist = _shortest_path_length_to_canteen(world, worker_manager, worker, building, blocked)
        if dist is None:
            continue
        pos = building.grid_pos
        gx, gy = pos if pos is not None else (10**9, 10**9)
        candidates.append((dist, gx, gy, building))

    if not candidates:
        return None

    candidates.sort(key=lambda t: (t[0], t[1], t[2], id(t[3])))
    _, _, _, chosen = candidates[0]
    if try_reserve_diner_slot(chosen, worker):
        return chosen
    return None
