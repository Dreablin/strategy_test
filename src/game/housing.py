"""Housing-domain helpers for population cap calculations."""

from __future__ import annotations

from typing import Any


def housing_town_hall(level: int) -> int:
    lvl = max(1, int(level))
    return 8 + 2 * (lvl - 1)


def housing_house(level: int) -> int:
    lvl = max(1, int(level))
    return 2 + 2 * (lvl - 1)


def current_population(registry: Any, worker_manager_or_count: Any) -> int:
    """Current occupied housing: spawned workers + queued school trainees."""
    if isinstance(worker_manager_or_count, int):
        workers_count = int(worker_manager_or_count)
    else:
        workers = getattr(worker_manager_or_count, "workers", None)
        workers_count = len(workers()) if callable(workers) else 0
    queued = 0
    for building in registry.all():
        if building.type_tag != "SCHOOL":
            continue
        queue_fn = getattr(building, "training_queue", None)
        if callable(queue_fn):
            queued += len(queue_fn())
    return workers_count + queued


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
