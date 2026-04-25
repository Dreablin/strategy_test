"""Workers and assignment (teleport); demolition orphans idle workers on a tile (PRD F-DEMO / F-WORK)."""

from __future__ import annotations

from game.buildings.base import Building


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
    """Tracks workers; notifies assignments when a staffed building is demolished."""

    __slots__ = ("_workers",)

    def __init__(self) -> None:
        self._workers: list[Worker] = []

    def add_worker(self, worker: Worker) -> None:
        self._workers.append(worker)

    def workers(self) -> tuple[Worker, ...]:
        return tuple(self._workers)

    def assign_to_building(self, worker: Worker, building: Building) -> None:
        worker.assigned_building = building
        worker.idle = False
        worker.stand_tile = building_center_tile(building)

    def is_staffed(self, building: Building) -> bool:
        return any(w.assigned_building is building for w in self._workers)

    def staffed_buildings(self) -> set[Building]:
        return {w.assigned_building for w in self._workers if w.assigned_building is not None}

    def notify_demolished(self, building: Building) -> None:
        """Park former workers on the demolished building's center tile (idle)."""
        cx, cy = building_center_tile(building)
        for w in self._workers:
            if w.assigned_building is building:
                w.assigned_building = None
                w.idle = True
                w.stand_tile = (cx, cy)

    def reassign_all(self) -> None:
        """Match idle workers to free buildings (implemented in T32/T33)."""
        return
