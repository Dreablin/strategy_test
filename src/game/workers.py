"""Workers and assignment (teleport); demolition orphans idle workers on a tile (PRD F-DEMO / F-WORK)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from game.buildings.base import Building
from game.config import TOWN_HALL_MIN_LEVEL_FOR_HIRE, WORKER_HIRE_COSTS, WORKER_TILE_TRAVEL_MS
from game.pathfinding import find_path_bfs
from game.resources import ResourceManager
from game.world import find_nearest_free_tree

CHOP_DURATION_MS = 10_000


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
        "carrying",
        "target_tree",
        "chop_started_ms",
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
        self.carrying: str | None = None
        self.target_tree: tuple[int, int] | None = None
        self.chop_started_ms = 0

    def start_move(self, path: list[tuple[int, int]], started_ms: int, *, move_state: str = "moving") -> None:
        if len(path) < 2:
            self.path = [self.current_tile, self.current_tile]
            self.target_tile = self.current_tile
            self.segment_started_ms = int(started_ms)
            self.segment_progress = 0.0
            if move_state == "going_to_tree":
                self.state = "going_to_tree"
            elif move_state == "returning":
                self.state = "returning"
            else:
                self.state = "working"
            self.idle = False
            return
        self.path = list(path)
        self.current_tile = self.path[0]
        self.target_tile = self.path[1]
        self.segment_started_ms = int(started_ms)
        self.segment_progress = 0.0
        self.state = move_state
        self.idle = False

    def update(self, now_ms: int) -> None:
        if self.state not in {"moving", "going_to_tree", "returning"} or self.target_tile is None:
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
            if self.state == "going_to_tree":
                self.state = "arrived_tree"
            elif self.state == "returning":
                self.state = "arrived_camp"
            else:
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
            if worker.state in {"moving", "going_to_tree", "returning"}:
                return "on the way"
            return "assigned"
        return "empty"

    def staffed_buildings(self) -> set[Building]:
        return {w.assigned_building for w in self._workers if w.assigned_building is not None}

    def working_buildings(self) -> set[Building]:
        return {
            w.assigned_building
            for w in self._workers
            if w.assigned_building is not None and w.state in {"working", "chopping", "depositing"}
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
        world = getattr(self._registry, "_world", None) if self._registry is not None else None
        for w in self._workers:
            if w.assigned_building is building:
                if world is not None:
                    world.release_reservations_for(w)
                w.assigned_building = None
                w.idle = True
                w.stand_tile = w.current_tile
                w.target_tile = None
                w.path = []
                w.segment_started_ms = 0
                w.segment_progress = 0.0
                w.state = "idle"
                w.carrying = None
                w.target_tree = None
                w.chop_started_ms = 0

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
                if worker.type_tag == "LUMBERJACK":
                    worker.assigned_building = target
                    assigned = self._start_lumberjack_cycle(worker, target, now_ms)
                    if assigned:
                        break
                    worker.assigned_building = None
                    continue
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
                worker.carrying = None
                worker.target_tree = None
                worker.chop_started_ms = 0

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
        world = getattr(self._registry, "_world", None) if self._registry is not None else None
        for worker in self._workers:
            worker.update(now_ms)
            if worker.type_tag != "LUMBERJACK":
                continue
            if world is None:
                continue
            camp = worker.assigned_building
            if camp is None:
                world.release_reservations_for(worker)
                continue

            if worker.state == "arrived_tree":
                worker.state = "chopping"
                worker.chop_started_ms = int(now_ms)
                continue

            if worker.state == "chopping":
                if int(now_ms) - worker.chop_started_ms < CHOP_DURATION_MS:
                    continue
                tree_tile = worker.target_tree
                if tree_tile is not None:
                    world.remove_tree(*tree_tile)
                worker.carrying = "wood"
                if not self._start_return_to_camp(worker, int(now_ms)):
                    worker.state = "depositing"
                continue

            if worker.state == "arrived_camp":
                worker.state = "depositing"
                continue

            if worker.state == "depositing":
                if worker.carrying == "wood" and self._resources is not None:
                    self._resources.add("wood", 1)
                    if hasattr(camp, "record_wood_delivered"):
                        camp.record_wood_delivered(1)
                worker.carrying = None
                worker.target_tree = None
                worker.chop_started_ms = 0
                if getattr(camp, "active", False):
                    self._start_lumberjack_cycle(worker, camp, int(now_ms))
                else:
                    worker.idle = True
                    worker.state = "idle"
                    worker.path = []
                    worker.target_tile = None
                    worker.segment_progress = 0.0

    def _start_lumberjack_cycle(self, worker: Worker, camp: Building, now_ms: int) -> bool:
        if self._registry is None:
            return False
        world = getattr(self._registry, "_world", None)
        if world is None:
            return False
        if not self._approach_tiles(camp):
            worker.idle = True
            worker.state = "idle"
            return False
        world.release_reservations_for(worker)
        blocked = {
            (x, y)
            for y in range(world.height)
            for x in range(world.width)
            if world.is_occupied(x, y)
        }
        blocked.discard(worker.current_tile)
        tree_tile = find_nearest_free_tree(world, worker.current_tile, blocked=blocked, skip_reserved=True)
        if tree_tile is None:
            worker.idle = True
            worker.state = "idle"
            return False
        if not world.reserve_tree(tree_tile[0], tree_tile[1], worker):
            worker.idle = True
            worker.state = "idle"
            return False

        tx, ty = tree_tile
        approach: tuple[int, int] | None = None
        best_len: int | None = None
        tree_blocked = set(blocked)
        tree_blocked.add(tree_tile)
        for ny in range(ty - 1, ty + 2):
            for nx in range(tx - 1, tx + 2):
                if (nx, ny) == tree_tile:
                    continue
                if not world.is_in_grass(nx, ny):
                    continue
                if world.is_occupied(nx, ny) or world.is_tree_blocking(nx, ny):
                    continue
                path = find_path_bfs(world, worker.current_tile, (nx, ny), tree_blocked)
                if path is None:
                    continue
                if best_len is None or len(path) < best_len:
                    best_len = len(path)
                    approach = (nx, ny)
        if approach is None:
            world.release_tree(*tree_tile)
            worker.idle = True
            worker.state = "idle"
            return False
        path = find_path_bfs(world, worker.current_tile, approach, tree_blocked)
        if path is None:
            world.release_tree(*tree_tile)
            worker.idle = True
            worker.state = "idle"
            return False
        worker.target_tree = tree_tile
        worker.start_move(path, started_ms=now_ms, move_state="going_to_tree")
        return True

    def _start_return_to_camp(self, worker: Worker, now_ms: int) -> bool:
        if self._registry is None or worker.assigned_building is None:
            return False
        world = getattr(self._registry, "_world", None)
        if world is None:
            return False
        blocked = {
            (x, y)
            for y in range(world.height)
            for x in range(world.width)
            if world.is_occupied(x, y)
        }
        blocked.discard(worker.current_tile)
        best_path: list[tuple[int, int]] | None = None
        for tile in self._approach_tiles(worker.assigned_building):
            path = find_path_bfs(world, worker.current_tile, tile, blocked)
            if path is None:
                continue
            if best_path is None or len(path) < len(best_path):
                best_path = path
        if best_path is None:
            return False
        worker.start_move(best_path, started_ms=now_ms, move_state="returning")
        return True
