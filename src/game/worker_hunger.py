"""Post-cycle hunger: try to reserve a reachable canteen before normal rest continues."""

from __future__ import annotations

from typing import TYPE_CHECKING

from game.config import HUNGER_SATIETY_THRESHOLD
from game.worker_models import Worker
from game.world import World

if TYPE_CHECKING:
    from game.buildings.registry import BuildingRegistry
    from game.workers import WorkerManager

BLOCKED_HUNGER_RETRY_MS = 4_000


def _try_hunger_reservation(
    worker: Worker,
    *,
    world: World,
    registry: BuildingRegistry,
    worker_manager: WorkerManager,
) -> bool:
    from game.canteen_selection import reserve_nearest_reachable_canteen_if_hungry

    if worker.carrying is not None:
        return False
    if int(worker.satiety) >= HUNGER_SATIETY_THRESHOLD:
        return False
    chosen = reserve_nearest_reachable_canteen_if_hungry(world, registry, worker_manager, worker)
    return chosen is not None


def try_blocked_cycle_hunger_check(
    worker: Worker,
    *,
    world: World,
    registry: BuildingRegistry,
    worker_manager: WorkerManager,
    now_ms: int,
) -> bool:
    """While a new work cycle cannot start, try canteen reservation on a throttled schedule."""
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
    return _try_hunger_reservation(
        worker,
        world=world,
        registry=registry,
        worker_manager=worker_manager,
    )


def try_builder_hunger_after_completion_or_idle(
    worker: Worker,
    *,
    world: World,
    registry: BuildingRegistry,
    worker_manager: WorkerManager,
    now_ms: int,
) -> bool:
    _ = int(now_ms)
    if worker.type_tag != "BUILDER":
        return False
    if worker.dining_canteen is not None:
        return False
    if worker.assigned_building is not None and worker.assigned_building.is_under_construction:
        return False
    if worker.state in {"building", "entering_site", "moving"}:
        return False
    if not worker.idle and worker.state != "idle":
        return False
    return _try_hunger_reservation(
        worker,
        world=world,
        registry=registry,
        worker_manager=worker_manager,
    )


def try_carrier_hunger_after_delivery_or_idle(
    worker: Worker,
    *,
    world: World,
    registry: BuildingRegistry,
    worker_manager: WorkerManager,
    now_ms: int,
) -> bool:
    _ = int(now_ms)
    if worker.type_tag != "CARRIER":
        return False
    if worker.dining_canteen is not None:
        return False
    if worker.transport_task is not None:
        return False
    if worker.carrying is not None:
        return False
    if not worker.idle and worker.state != "idle":
        return False
    return _try_hunger_reservation(
        worker,
        world=world,
        registry=registry,
        worker_manager=worker_manager,
    )


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
    return _try_hunger_reservation(
        worker,
        world=world,
        registry=registry,
        worker_manager=worker_manager,
    )
