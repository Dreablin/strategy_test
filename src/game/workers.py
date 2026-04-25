"""Workers and assignment (teleport); demolition orphans idle workers on a tile (PRD F-DEMO / F-WORK)."""

from __future__ import annotations

from typing import Any

from game.buildings.base import Building
from game.config import WORKER_HIRE_COST
from game.resources import ResourceManager


def building_center_tile(building: Building) -> tuple[int, int]:
    """Integer grid cell at the footprint center (for stand / orphan position)."""
    pos = building.grid_pos
    if pos is None:
        raise ValueError("building has no grid position")
    gx, gy = pos
    w, h = type(building).footprint
    return gx + w // 2, gy + h // 2


class Worker:
    """One worker: type tag, optional assigned building, idle flag, stand tile for rendering."""

    __slots__ = ("type_tag", "assigned_building", "idle", "stand_tile")

    def __init__(self, type_tag: str, *, stand_tile: tuple[int, int] = (0, 0)) -> None:
        self.type_tag = type_tag
        self.assigned_building: Building | None = None
        self.idle = True
        self.stand_tile: tuple[int, int] = stand_tile


class WorkerManager:
    """Tracks workers; notifies assignments when a staffed building is demolished (PRD F-WORK)."""

    __slots__ = ("_registry", "_resources", "_workers")
    _WORKER_TO_BUILDING: dict[str, str] = {
        "LUMBERJACK": "LUMBER_CAMP",
        "STONECUTTER": "STONE_MINE",
        "MINER": "IRON_MINE",
        "FARMER": "FARM",
    }

    def __init__(
        self,
        resources: ResourceManager | None = None,
        registry: Any | None = None,
    ) -> None:
        self._resources = resources
        self._registry = registry
        self._workers: list[Worker] = []

    def add_worker(self, worker: Worker) -> None:
        self._workers.append(worker)

    def workers(self) -> tuple[Worker, ...]:
        return tuple(self._workers)

    def idle(self) -> list[Worker]:
        """Idle workers (PRD ``WorkerManager.idle``)."""
        return [w for w in self._workers if w.idle]

    def assign_to_building(self, worker: Worker, building: Building) -> None:
        worker.assigned_building = building
        worker.idle = False
        worker.stand_tile = building_center_tile(building)

    def is_staffed(self, building: Building) -> bool:
        return any(w.assigned_building is building for w in self._workers)

    def staffed_buildings(self) -> set[Building]:
        return {w.assigned_building for w in self._workers if w.assigned_building is not None}

    def hire(self, worker_type: str) -> Worker | None:
        """Hire a worker for 50 food; ``None`` if unaffordable."""
        if self._resources is None or self._registry is None:
            return None
        if worker_type not in self._WORKER_TO_BUILDING:
            return None
        if not self._resources.try_spend(WORKER_HIRE_COST):
            return None
        town_hall = next((b for b in self._registry.all() if b.type_tag == "TOWN_HALL"), None)
        stand = building_center_tile(town_hall) if town_hall is not None else (0, 0)
        worker = Worker(worker_type, stand_tile=stand)
        self._workers.append(worker)
        return worker

    def notify_demolished(self, building: Building) -> None:
        """Park former workers on the demolished building's center tile (idle)."""
        cx, cy = building_center_tile(building)
        for w in self._workers:
            if w.assigned_building is building:
                w.assigned_building = None
                w.idle = True
                w.stand_tile = (cx, cy)

    def reassign_all(self) -> None:
        """Assign one idle worker per free matching building."""
        if self._registry is None:
            return
        for worker in [w for w in self._workers if w.idle]:
            want = self._WORKER_TO_BUILDING.get(worker.type_tag)
            if want is None:
                continue
            target = next(
                (
                    b
                    for b in self._registry.all()
                    if b.type_tag == want and not self.is_staffed(b)
                ),
                None,
            )
            if target is not None:
                self.assign_to_building(worker, target)
