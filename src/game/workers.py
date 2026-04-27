"""Workers and assignment (teleport); demolition orphans idle workers on a tile (PRD F-DEMO / F-WORK)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from game.buildings.base import Building
from game.config import TOWN_HALL_MIN_LEVEL_FOR_HIRE, WORKER_HIRE_COSTS, WORKER_TILE_TRAVEL_MS
from game.pathfinding import find_path_bfs
from game.resources import ResourceManager


def building_center_tile(building: Building) -> tuple[int, int]:
    """Integer grid cell at the footprint center (for stand / orphan position)."""
    pos = building.grid_pos
    if pos is None:
        raise ValueError("building has no grid position")
    gx, gy = pos
    w, h = type(building).footprint
    return gx + w // 2, gy + h // 2


def town_hall_spawn_tile(building: Building) -> tuple[int, int]:
    """Deterministic spawn tile: one cell directly below Town Hall footprint."""
    pos = building.grid_pos
    if pos is None:
        raise ValueError("building has no grid position")
    gx, gy = pos
    w, h = type(building).footprint
    return gx + w // 2, gy + h


class Worker:
    """One worker: type tag, optional assigned building, idle flag, stand tile for rendering."""

    __slots__ = (
        "type_tag",
        "assigned_building",
        "idle",
        "stand_tile",
        "state",
        "current_tile",
        "target_tile",
        "path",
        "segment_started_ms",
        "segment_progress",
    )

    def __init__(self, type_tag: str, *, stand_tile: tuple[int, int] = (17, 19)) -> None:
        self.type_tag = type_tag
        self.assigned_building: Building | None = None
        self.idle = True
        self.stand_tile: tuple[int, int] = stand_tile
        self.state = "idle"
        self.current_tile = stand_tile
        self.target_tile: tuple[int, int] | None = None
        self.path: list[tuple[int, int]] = []
        self.segment_started_ms = 0
        self.segment_progress = 0.0

    def start_move(self, path: list[tuple[int, int]], started_ms: int) -> None:
        if len(path) < 2:
            self.path = []
            self.target_tile = self.current_tile
            self.segment_progress = 0.0
            self.state = "working"
            self.idle = False
            return
        self.path = list(path)
        self.current_tile = self.path[0]
        self.target_tile = self.path[1]
        self.segment_started_ms = int(started_ms)
        self.segment_progress = 0.0
        self.state = "moving"
        self.idle = False

    def update(self, now_ms: int) -> None:
        if self.state != "moving" or self.target_tile is None:
            return
        elapsed = max(0, int(now_ms) - self.segment_started_ms)
        while elapsed >= WORKER_TILE_TRAVEL_MS:
            self.current_tile = self.target_tile
            self.path = self.path[1:] if self.path else []
            if len(self.path) >= 2:
                self.target_tile = self.path[1]
                self.segment_started_ms += WORKER_TILE_TRAVEL_MS
                self.segment_progress = 0.0
                elapsed = max(0, int(now_ms) - self.segment_started_ms)
                continue
            self.target_tile = self.current_tile
            self.segment_progress = 1.0
            self.state = "working"
            self.idle = False
            self.stand_tile = self.current_tile
            return
        self.segment_progress = elapsed / WORKER_TILE_TRAVEL_MS


class WorkerManager:
    """Tracks workers; notifies assignments when a staffed building is demolished (PRD F-WORK)."""

    __slots__ = ("_now_ms_fn", "_registry", "_resources", "_workers")
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
        now_ms_fn: Callable[[], int] | None = None,
    ) -> None:
        self._resources = resources
        self._registry = registry
        self._workers: list[Worker] = []
        self._now_ms_fn = now_ms_fn or (lambda: 0)

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
        worker.current_tile = worker.stand_tile
        worker.target_tile = worker.current_tile
        worker.path = []
        worker.segment_started_ms = 0
        worker.segment_progress = 0.0
        worker.state = "working"

    def is_staffed(self, building: Building) -> bool:
        return any(w.assigned_building is building for w in self._workers)

    def worker_status_for_building(self, building: Building) -> str:
        """Return panel-friendly worker status: empty | on the way | assigned."""
        for worker in self._workers:
            if worker.assigned_building is not building:
                continue
            if worker.state == "moving":
                return "on the way"
            return "assigned"
        return "empty"

    def staffed_buildings(self) -> set[Building]:
        return {w.assigned_building for w in self._workers if w.assigned_building is not None}

    def working_buildings(self) -> set[Building]:
        return {
            w.assigned_building
            for w in self._workers
            if w.assigned_building is not None and w.state == "working"
        }

    def hire(self, worker_type: str) -> Worker | None:
        """Hire a worker if town hall level and resources allow it."""
        if self._resources is None or self._registry is None:
            return None
        if worker_type not in self._WORKER_TO_BUILDING:
            return None
        min_level = int(TOWN_HALL_MIN_LEVEL_FOR_HIRE.get(worker_type, 1))
        th_level = 0
        for b in self._registry.all():
            if b.type_tag == "TOWN_HALL":
                th_level = b.level
                break
        if th_level < min_level:
            return None
        cost = dict(WORKER_HIRE_COSTS.get(worker_type, {"food": 0}))
        if not self._resources.try_spend(cost):
            return None
        town_hall = next((b for b in self._registry.all() if b.type_tag == "TOWN_HALL"), None)
        stand = (17, 19)
        if town_hall is not None:
            stand = town_hall_spawn_tile(town_hall)
            world = getattr(self._registry, "_world", None)
            if world is not None and (
                not world.is_in_grass(*stand) or world.is_occupied(*stand)
            ):
                approaches = self._approach_tiles(town_hall)
                if approaches:
                    stand = approaches[0]
                else:
                    stand = building_center_tile(town_hall)
        worker = Worker(worker_type, stand_tile=stand)
        self._workers.append(worker)
        return worker

    def can_hire(self, worker_type: str) -> bool:
        """Whether current state allows hiring this worker type."""
        if self._resources is None or self._registry is None:
            return False
        if worker_type not in self._WORKER_TO_BUILDING:
            return False
        min_level = int(TOWN_HALL_MIN_LEVEL_FOR_HIRE.get(worker_type, 1))
        th_level = 0
        for b in self._registry.all():
            if b.type_tag == "TOWN_HALL":
                th_level = b.level
                break
        cost = dict(WORKER_HIRE_COSTS.get(worker_type, {"food": 0}))
        return th_level >= min_level and self._resources.has(cost)

    def notify_demolished(self, building: Building) -> None:
        """Workers targeting this building become idle at their current tile."""
        for w in self._workers:
            if w.assigned_building is building:
                w.assigned_building = None
                w.idle = True
                w.stand_tile = w.current_tile
                w.target_tile = None
                w.path = []
                w.segment_started_ms = 0
                w.segment_progress = 0.0
                w.state = "idle"

    def reassign_all(self) -> None:
        """Assign one idle worker per free matching building with path-to-approach."""
        if self._registry is None:
            return
        world = getattr(self._registry, "_world", None)
        if world is None:
            return
        now_ms = int(self._now_ms_fn())
        for worker in [w for w in self._workers if w.idle]:
            want = self._WORKER_TO_BUILDING.get(worker.type_tag)
            if want is None:
                continue
            targets = [b for b in self._registry.all() if b.type_tag == want and not self.is_staffed(b)]
            assigned = False
            blocked = {
                (x, y)
                for y in range(world.height)
                for x in range(world.width)
                if world.is_occupied(x, y)
            }
            blocked.update({(x, y) for (x, y), _tree in world.iter_alive_trees()})
            # Workers may start on an occupied spawn tile (e.g., Town Hall center).
            blocked.discard(worker.current_tile)
            for target in targets:
                best_path: list[tuple[int, int]] | None = None
                for tile in self._approach_tiles(target):
                    path = find_path_bfs(world, worker.current_tile, tile, blocked)
                    if path is None:
                        continue
                    if best_path is None or len(path) < len(best_path):
                        best_path = path
                if best_path is None:
                    continue
                worker.assigned_building = target
                worker.start_move(best_path, started_ms=now_ms)
                assigned = True
                break
            if not assigned:
                worker.assigned_building = None
                worker.idle = True
                worker.state = "idle"
                worker.path = []
                worker.target_tile = None
                worker.segment_progress = 0.0

    def _approach_tiles(self, building: Building) -> list[tuple[int, int]]:
        pos = building.grid_pos
        if pos is None or self._registry is None:
            return []
        world = getattr(self._registry, "_world", None)
        if world is None:
            return []
        gx, gy = pos
        w, h = type(building).footprint
        x0, x1 = gx - 1, gx + w
        y0, y1 = gy - 1, gy + h
        tiles: list[tuple[int, int]] = []
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                inside = gx <= x < gx + w and gy <= y < gy + h
                if inside:
                    continue
                if not world.is_in_grass(x, y):
                    continue
                if world.is_occupied(x, y):
                    continue
                if world.is_tree_blocking(x, y):
                    continue
                tiles.append((x, y))
        return tiles

    def update(self, now_ms: int) -> None:
        """Advance worker movement interpolation/state for this frame."""
        for worker in self._workers:
            worker.update(now_ms)
