"""Laboratory scientist staffing helpers for WorkerManager."""

from __future__ import annotations

from collections.abc import Sequence

from game.buildings.base import Building
from game.worker_models import Worker

_SCIENTIST_TAG = "SCIENTIST"
_LABORATORY_TAG = "LABORATORY"


def laboratory_assigned_scientists(
    workers: Sequence[Worker],
    laboratory: Building,
) -> tuple[Worker, ...]:
    """Scientists currently assigned to this Laboratory."""
    if laboratory.type_tag != _LABORATORY_TAG:
        return ()
    return tuple(
        worker
        for worker in workers
        if worker.type_tag == _SCIENTIST_TAG and worker.assigned_building is laboratory
    )


def laboratory_assigned_scientist_count(workers: Sequence[Worker], laboratory: Building) -> int:
    return len(laboratory_assigned_scientists(workers, laboratory))


def laboratory_free_scientist_slots(workers: Sequence[Worker], laboratory: Building) -> int:
    if laboratory.type_tag != _LABORATORY_TAG:
        return 0
    capacity_fn = getattr(laboratory, "scientist_slot_capacity", None)
    if not callable(capacity_fn):
        return 0
    capacity = int(capacity_fn())
    assigned = laboratory_assigned_scientist_count(workers, laboratory)
    return max(0, capacity - assigned)
