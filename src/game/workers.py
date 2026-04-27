"""Workers and assignment (teleport); demolition orphans idle workers on a tile (PRD F-DEMO / F-WORK)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from game.buildings.base import Building
from game.characteristics import Characteristics
from game.config import TOWN_HALL_MIN_LEVEL_FOR_HIRE, WORKER_HIRE_COSTS, WORKER_TILE_TRAVEL_MS
from game.pathfinding import find_path_bfs
from game.resources import ResourceManager
from game.world import find_nearest_free_stone, find_nearest_free_tree

CHOP_DURATION_MS = 10_000
MINE_DURATION_MS = 10_000
LUMBERJACK_REST_MS = 5_000
STONECUTTER_REST_MS = 5_000
MOVE_SPEED_PER_LEVEL = 0.05
GATHER_SPEED_PER_LEVEL = 0.05


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
        "arrival_ms",
        "camp_wait_until_ms",
        "carrying",
        "target_tree",
        "chop_started_ms",
        "chop_duration_ms",
        "characteristics",
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
        self.arrival_ms = 0
        self.camp_wait_until_ms = 0
        self.carrying: str | None = None
        self.target_tree: tuple[int, int] | None = None
        self.chop_started_ms = 0
        self.chop_duration_ms = CHOP_DURATION_MS
        self.characteristics = Characteristics()

    def start_move(self, path: list[tuple[int, int]], started_ms: int, *, move_state: str = "moving") -> None:
        if len(path) < 2:
            self.path = [self.current_tile, self.current_tile]
            self.target_tile = self.current_tile
            self.segment_started_ms = int(started_ms)
            self.arrival_ms = int(started_ms)
            self.segment_progress = 0.0
            if move_state == "going_to_tree":
                self.state = "going_to_tree"
            elif move_state == "going_to_stone":
                self.state = "going_to_stone"
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
        if self.state not in {"moving", "going_to_tree", "going_to_stone", "returning"} or self.target_tile is None:
            return
        travel_ms = self._effective_travel_ms()
        elapsed = max(0, int(now_ms) - self.segment_started_ms)
        while elapsed >= travel_ms:
            self.current_tile = self.target_tile
            self.path = self.path[1:] if self.path else []
            if len(self.path) >= 2:
                self.target_tile = self.path[1]
                self.segment_started_ms += travel_ms
                self.segment_progress = 0.0
                elapsed = max(0, int(now_ms) - self.segment_started_ms)
                continue
            self.target_tile = self.current_tile
            self.segment_progress = 1.0
            self.arrival_ms = self.segment_started_ms + travel_ms
            if self.state == "going_to_tree":
                self.state = "arrived_tree"
            elif self.state == "going_to_stone":
                self.state = "arrived_stone"
            elif self.state == "returning":
                self.state = "arrived_camp"
            else:
                self.state = "working"
            self.idle = False
            self.stand_tile = self.current_tile
            return
        self.segment_progress = elapsed / travel_ms

    def _effective_travel_ms(self) -> int:
        speed = self.characteristics.move_speed_mult
        if speed <= 0.0:
            return WORKER_TILE_TRAVEL_MS
        return max(1, int(round(WORKER_TILE_TRAVEL_MS / speed)))


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
        if registry is not None and hasattr(registry, "bind_worker_manager"):
            registry.bind_worker_manager(self)

    def add_worker(self, worker: Worker) -> None:
        self._workers.append(worker)

    def workers(self) -> tuple[Worker, ...]:
        return tuple(self._workers)

    def idle(self) -> list[Worker]:
        """Idle workers (PRD ``WorkerManager.idle``)."""
        return [w for w in self._workers if w.idle]

    def assign_to_building(self, worker: Worker, building: Building) -> None:
        self._clear_building_bonus(worker)
        worker.assigned_building = building
        worker.idle = False
        worker.stand_tile = building_center_tile(building)
        worker.current_tile = worker.stand_tile
        worker.target_tile = worker.current_tile
        worker.path = []
        worker.segment_started_ms = 0
        worker.segment_progress = 0.0
        worker.state = "working"
        self._apply_building_bonus(worker, building)

    def is_staffed(self, building: Building) -> bool:
        return any(w.assigned_building is building for w in self._workers)

    def worker_status_for_building(self, building: Building) -> str:
        """Return panel-friendly worker status: empty | on the way | assigned."""
        for worker in self._workers:
            if worker.assigned_building is not building:
                continue
            if worker.state in {"moving", "going_to_tree", "going_to_stone", "returning"}:
                return "on the way"
            return "assigned"
        return "empty"

    def production_status_for_building(self, building: Building) -> str:
        """Human-readable production status for building panels."""
        if not (hasattr(building, "storage_capacity") and hasattr(building, "stored")):
            return "N/A"

        worker: Worker | None = None
        for candidate in self._workers:
            if candidate.assigned_building is building:
                worker = candidate
                break
        if worker is None:
            return "No worker"

        if hasattr(building, "active") and not bool(getattr(building, "active")):
            return "Inactive"
        if hasattr(building, "is_storage_full") and building.is_storage_full():
            return "Storage full"

        moving_states = {"moving", "going_to_tree", "going_to_stone", "returning"}
        if worker.state in moving_states:
            return "On the way"
        if worker.state in {"chopping", "mining"}:
            return "Gathering"
        if worker.state == "depositing":
            return "Depositing"
        if worker.state in {"arrived_tree", "arrived_stone"}:
            return "At resource"
        if worker.state == "arrived_camp":
            return "At camp"
        if worker.state == "working":
            now_ms = int(self._now_ms_fn())
            if worker.camp_wait_until_ms > now_ms:
                return "Resting"
            return "Ready"
        if worker.state == "idle":
            return "Waiting target"
        return "Unknown"

    def staffed_buildings(self) -> set[Building]:
        return {w.assigned_building for w in self._workers if w.assigned_building is not None}

    def working_buildings(self) -> set[Building]:
        return {
            w.assigned_building
            for w in self._workers
            if w.assigned_building is not None
            and w.state in {"working", "chopping", "mining", "depositing"}
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
                self._clear_building_bonus(w)
                w.assigned_building = None
                w.idle = True
                w.stand_tile = w.current_tile
                w.target_tile = None
                w.path = []
                w.segment_started_ms = 0
                w.segment_progress = 0.0
                w.state = "idle"
                w.camp_wait_until_ms = 0
                w.carrying = None
                w.target_tree = None
                w.chop_started_ms = 0
                w.chop_duration_ms = CHOP_DURATION_MS

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
            # Gather worker already at its camp (e.g., post-deposit with toggle off, then on):
            # resume the gather cycle directly without walking back to the camp.
            if (
                worker.type_tag in {"LUMBERJACK", "STONECUTTER"}
                and worker.assigned_building is not None
                and worker.assigned_building.type_tag == want
            ):
                camp = worker.assigned_building
                self._park_worker_inside_camp(worker, camp)
                rest_ms = LUMBERJACK_REST_MS if worker.type_tag == "LUMBERJACK" else STONECUTTER_REST_MS
                worker.camp_wait_until_ms = max(worker.camp_wait_until_ms, now_ms + rest_ms)
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
            blocked.update({(x, y) for (x, y), _stone in world.iter_stones()})
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
                self._apply_building_bonus(worker, target)
                worker.start_move(best_path, started_ms=now_ms)
                assigned = True
                break
            if not assigned:
                self._clear_building_bonus(worker)
                worker.assigned_building = None
                worker.idle = True
                worker.state = "idle"
                worker.path = []
                worker.target_tile = None
                worker.segment_progress = 0.0
                worker.camp_wait_until_ms = 0
                worker.carrying = None
                worker.target_tree = None
                worker.chop_started_ms = 0
                worker.chop_duration_ms = CHOP_DURATION_MS

    def refresh_worker_bonuses(self) -> None:
        """Recompute building-level permanent bonuses for assigned workers."""
        for worker in self._workers:
            self._clear_building_bonus(worker)
            if worker.assigned_building is not None and not worker.idle:
                self._apply_building_bonus(worker, worker.assigned_building)

    def refresh_building_bonuses(self, building: Building) -> None:
        """Refresh permanent level bonuses for workers assigned to one building."""
        for worker in self._workers:
            if worker.assigned_building is not building:
                continue
            self._clear_building_bonus(worker)
            if not worker.idle:
                self._apply_building_bonus(worker, building)

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
            if worker.type_tag not in {"LUMBERJACK", "STONECUTTER"}:
                continue
            if world is None:
                continue
            camp = worker.assigned_building
            if camp is None:
                world.release_reservations_for(worker)
                continue

            gather_state = self._gather_state_for(worker.type_tag)
            if gather_state is None:
                continue

            # Gather worker just walked into the camp: kick off the cycle from the
            # actual arrival timestamp so leftover time in this tick still moves the
            # worker further along the new (resource-targeting) path.
            if worker.state == "working":
                self._park_worker_inside_camp(worker, camp)
                if worker.camp_wait_until_ms <= 0:
                    worker.camp_wait_until_ms = worker.arrival_ms + gather_state["rest_ms"]
                if int(now_ms) < worker.camp_wait_until_ms:
                    continue
                if not getattr(camp, "active", False):
                    continue
                if hasattr(camp, "is_storage_full") and camp.is_storage_full():
                    # Keep waiting inside the camp while storage is full.
                    worker.camp_wait_until_ms = int(now_ms) + 1_000
                    continue
                depart_ms = worker.camp_wait_until_ms
                if not self._start_gather_cycle(worker, camp, depart_ms, world_query=gather_state["world_query"]):
                    # No target/path right now: stay inside camp and retry later.
                    self._park_worker_inside_camp(worker, camp)
                    worker.camp_wait_until_ms = int(now_ms) + 1_000
                    continue
                worker.camp_wait_until_ms = 0
                worker.update(now_ms)

            if worker.state == gather_state["arrived_state"]:
                worker.state = gather_state["work_state"]
                worker.chop_started_ms = int(now_ms)
                speed = worker.characteristics.gather_speed_mult
                if speed <= 0.0:
                    worker.chop_duration_ms = gather_state["duration_ms"]
                else:
                    worker.chop_duration_ms = max(1, int(round(gather_state["duration_ms"] / speed)))
                continue

            if worker.state == gather_state["work_state"]:
                if int(now_ms) - worker.chop_started_ms < worker.chop_duration_ms:
                    continue
                target_tile = worker.target_tree
                if target_tile is not None:
                    if gather_state["world_query"] == "tree":
                        world.remove_tree(*target_tile)
                    else:
                        world.harvest_stone(*target_tile)
                worker.carrying = gather_state["carry_resource"]
                if not self._start_return_to_camp(worker, int(now_ms)):
                    worker.state = "depositing"
                continue

            if worker.state == "arrived_camp":
                self._park_worker_inside_camp(worker, camp)
                worker.state = "depositing"
                continue

            if worker.state == "depositing":
                if worker.carrying == gather_state["carry_resource"] and self._resources is not None:
                    self._resources.add(gather_state["carry_resource"], 1)
                    if hasattr(camp, "add_to_storage"):
                        camp.add_to_storage(1)
                    if hasattr(camp, gather_state["record_method"]):
                        record_method = getattr(camp, gather_state["record_method"])
                        record_method(1)
                worker.carrying = None
                worker.target_tree = None
                worker.chop_started_ms = 0
                worker.chop_duration_ms = CHOP_DURATION_MS
                self._park_worker_inside_camp(worker, camp)
                worker.camp_wait_until_ms = int(now_ms) + gather_state["rest_ms"]
                continue
    def _gather_state_for(self, worker_type: str) -> dict[str, Any] | None:
        if worker_type == "LUMBERJACK":
            return {
                "world_query": "tree",
                "arrived_state": "arrived_tree",
                "work_state": "chopping",
                "duration_ms": CHOP_DURATION_MS,
                "carry_resource": "wood",
                "record_method": "record_wood_delivered",
                "rest_ms": LUMBERJACK_REST_MS,
            }
        if worker_type == "STONECUTTER":
            return {
                "world_query": "stone",
                "arrived_state": "arrived_stone",
                "work_state": "mining",
                "duration_ms": MINE_DURATION_MS,
                "carry_resource": "stone",
                "record_method": "record_stone_delivered",
                "rest_ms": STONECUTTER_REST_MS,
            }
        return None

    def _start_lumberjack_cycle(self, worker: Worker, camp: Building, now_ms: int) -> bool:
        return self._start_gather_cycle(worker, camp, now_ms, world_query="tree")

    def _start_gather_cycle(
        self, worker: Worker, camp: Building, now_ms: int, *, world_query: str
    ) -> bool:
        if self._registry is None:
            return False
        world = getattr(self._registry, "_world", None)
        if world is None:
            return False
        if not self._approach_tiles(camp):
            worker.idle = True
            worker.state = "idle"
            self._clear_building_bonus(worker)
            return False
        world.release_reservations_for(worker)
        blocked = {
            (x, y)
            for y in range(world.height)
            for x in range(world.width)
            if world.is_occupied(x, y)
        }
        blocked.discard(worker.current_tile)
        rejected_targets: set[tuple[int, int]] = set()
        while True:
            target_tile = self._find_nearest_gather_target(
                world,
                worker.current_tile,
                blocked=blocked,
                world_query=world_query,
                skip_targets=rejected_targets,
            )
            if target_tile is None:
                worker.idle = True
                worker.state = "idle"
                self._clear_building_bonus(worker)
                return False
            tx, ty = target_tile
            reserve_ok = (
                world.reserve_tree(tx, ty, worker)
                if world_query == "tree"
                else world.reserve_stone(tx, ty, worker)
            )
            if not reserve_ok:
                rejected_targets.add(target_tile)
                continue

            approach: tuple[int, int] | None = None
            best_len: int | None = None
            target_blocked = set(blocked)
            target_blocked.add(target_tile)
            for ny in range(ty - 1, ty + 2):
                for nx in range(tx - 1, tx + 2):
                    if (nx, ny) == target_tile:
                        continue
                    if not world.is_in_grass(nx, ny):
                        continue
                    if world.is_occupied(nx, ny) or world.is_tree_blocking(nx, ny) or world.is_stone_blocking(nx, ny):
                        continue
                    path = find_path_bfs(world, worker.current_tile, (nx, ny), target_blocked)
                    if path is None:
                        continue
                    if best_len is None or len(path) < best_len:
                        best_len = len(path)
                        approach = (nx, ny)
            if approach is None:
                if world_query == "tree":
                    world.release_tree(*target_tile)
                else:
                    world.release_stone(*target_tile)
                rejected_targets.add(target_tile)
                continue
            path = find_path_bfs(world, worker.current_tile, approach, target_blocked)
            if path is None:
                if world_query == "tree":
                    world.release_tree(*target_tile)
                else:
                    world.release_stone(*target_tile)
                rejected_targets.add(target_tile)
                continue
            worker.target_tree = target_tile
            move_state = "going_to_tree" if world_query == "tree" else "going_to_stone"
            worker.start_move(path, started_ms=now_ms, move_state=move_state)
            return True

    @staticmethod
    def _find_nearest_gather_target(
        world: Any,
        from_tile: tuple[int, int],
        *,
        blocked: set[tuple[int, int]],
        world_query: str,
        skip_targets: set[tuple[int, int]] | None = None,
    ) -> tuple[int, int] | None:
        if world_query == "tree":
            return find_nearest_free_tree(
                world,
                from_tile,
                blocked=blocked,
                skip_reserved=True,
                skip_targets=skip_targets,
            )
        if world_query == "stone":
            return find_nearest_free_stone(
                world,
                from_tile,
                blocked=blocked,
                skip_reserved=True,
                skip_targets=skip_targets,
            )
        return None

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

    def _park_worker_inside_camp(self, worker: Worker, camp: Building) -> None:
        world = getattr(self._registry, "_world", None) if self._registry is not None else None
        if world is not None and world.is_occupied(*worker.current_tile):
            approach_tiles = self._approach_tiles(camp)
            if approach_tiles:
                worker.current_tile = approach_tiles[0]
        worker.stand_tile = worker.current_tile
        worker.target_tile = worker.current_tile
        worker.path = []
        worker.segment_progress = 0.0
        worker.idle = False
        worker.state = "working"

    @staticmethod
    def _building_bonus_source(building: Building) -> tuple[str, int]:
        return ("building_level", id(building))

    def _clear_building_bonus(self, worker: Worker) -> None:
        building = worker.assigned_building
        if building is None:
            return
        worker.characteristics.remove_source(self._building_bonus_source(building))

    def _apply_building_bonus(self, worker: Worker, building: Building) -> None:
        delta = (building.level - 1) * MOVE_SPEED_PER_LEVEL
        source = self._building_bonus_source(building)
        worker.characteristics.add_permanent(source, "move_speed_mult", delta)
        gather_delta = (building.level - 1) * GATHER_SPEED_PER_LEVEL
        worker.characteristics.add_permanent(source, "gather_speed_mult", gather_delta)
