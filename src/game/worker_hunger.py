"""Post-cycle hunger: try to reserve a reachable canteen before normal rest continues."""

from __future__ import annotations

from typing import TYPE_CHECKING

from game.worker_models import Worker
from game.world import World

if TYPE_CHECKING:
    from game.buildings.registry import BuildingRegistry
    from game.workers import WorkerManager

BLOCKED_HUNGER_RETRY_MS = 4_000


def try_blocked_cycle_hunger_check(
    worker: Worker,
    *,
    world: World,
    registry: BuildingRegistry,
    worker_manager: WorkerManager,
    now_ms: int,
) -> bool:
    """While a new work cycle cannot start, try canteen reservation on a throttled schedule."""
    from game.canteen_selection import (
        HUNGER_SATIETY_THRESHOLD,
        reserve_nearest_reachable_canteen_if_hungry,
    )

    now_ms = int(now_ms)
    if worker.carrying is not None:
        return False
    if int(worker.satiety) >= HUNGER_SATIETY_THRESHOLD:
        return False
    if worker.dining_canteen is not None:
        return False
    last = int(worker.blocked_cycle_hunger_try_ms)
    if last >= 0 and now_ms - last < BLOCKED_HUNGER_RETRY_MS:
        return False
    worker.blocked_cycle_hunger_try_ms = now_ms
    chosen = reserve_nearest_reachable_canteen_if_hungry(world, registry, worker_manager, worker)
    return chosen is not None


def try_hunger_canteen_after_completed_cycle(
    worker: Worker,
    *,
    world: World,
    registry: BuildingRegistry,
    worker_manager: WorkerManager,
    now_ms: int,
) -> bool:
    """If hungry, reserve nearest reachable canteen. Call only right after a work cycle completes."""
    worker.blocked_cycle_hunger_try_ms = -1
    _ = int(now_ms)  # reserved for future throttled retries (Phase 22.5)
    from game.canteen_selection import (
        HUNGER_SATIETY_THRESHOLD,
        reserve_nearest_reachable_canteen_if_hungry,
    )

    if worker.carrying is not None:
        return False
    if int(worker.satiety) >= HUNGER_SATIETY_THRESHOLD:
        return False
    chosen = reserve_nearest_reachable_canteen_if_hungry(world, registry, worker_manager, worker)
    return chosen is not None
