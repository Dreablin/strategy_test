"""Post-cycle hunger: try to reserve a reachable canteen before normal rest continues."""

from __future__ import annotations

from typing import TYPE_CHECKING

from game.worker_models import Worker
from game.world import World

if TYPE_CHECKING:
    from game.buildings.registry import BuildingRegistry
    from game.workers import WorkerManager


def try_hunger_canteen_after_completed_cycle(
    worker: Worker,
    *,
    world: World,
    registry: BuildingRegistry,
    worker_manager: WorkerManager,
    now_ms: int,
) -> bool:
    """If hungry, reserve nearest reachable canteen. Call only right after a work cycle completes."""
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
