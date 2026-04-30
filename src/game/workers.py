"""Workers and assignment (teleport); demolition orphans idle workers on a tile (PRD F-DEMO / F-WORK)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import random
from typing import Any

from game.buildings.base import Building
from game.buildings.school import School
from game.buildings.town_hall import TownHall
from game.characteristics import Characteristics
from game.config import (
    GATHER_RESOURCE_SEARCH_RADIUS,
    TOWN_HALL_MIN_LEVEL_FOR_HIRE,
    WORKER_TILE_TRAVEL_MS,
)
from game.construction import complete_construction
from game.housing import current_population, max_population
from game.pathfinding import find_path_bfs
from game.world import find_nearest_free_stone, find_nearest_free_tree

CHOP_DURATION_MS = 10_000
MINE_DURATION_MS = 10_000
PLANT_DURATION_MS = 5_000
LUMBERJACK_REST_MS = 5_000
STONECUTTER_REST_MS = 5_000
FORESTER_REST_MS = 5_000
FORESTER_TARGET_RANDOM_TRIES = 3
FORESTER_TARGET_RETRY_MS = 1_000
FORESTER_RETURN_RETRY_MS = 3_000
CARRIER_INTERACT_MS = 2_000
SAWMILL_BASE_CYCLE_MS = 30_000
SAWMILL_MIN_CYCLE_MS = 5_000
SAWYER_REST_MS = 10_000
MOVE_SPEED_PER_LEVEL = 0.05
GATHER_SPEED_PER_LEVEL = 0.05


@dataclass(slots=True)
class TransportTask:
    resource: str
    source: Building
    target: Building
    priority: int = 0


def construction_transport_tasks(registry: Any) -> list[TransportTask]:
    """Build high-priority transport tasks from Town Hall to construction sites."""
    if registry is None:
        return []
    buildings = list(registry.all())
    town_hall = next((b for b in buildings if b.type_tag == "TOWN_HALL"), None)
    if town_hall is None or not hasattr(town_hall, "warehouse_amount"):
        return []
    tasks: list[TransportTask] = []
    for building in buildings:
        if not getattr(building, "is_under_construction", False):
            continue
        site = getattr(building, "construction_site", None)
        if site is None:
            continue
        for resource, need in site.remaining_resources().items():
            available = int(town_hall.warehouse_amount(resource))
            count = min(int(need), max(0, available))
            for _ in range(count):
                tasks.append(
                    TransportTask(
                        resource=str(resource),
                        source=town_hall,
                        target=building,
                        priority=10,
                    )
                )
    return tasks


def sawmill_input_transport_tasks(registry: Any) -> list[TransportTask]:
    """Build low-priority refill tasks from Town Hall to active sawmills."""
    if registry is None:
        return []
    buildings = list(registry.all())
    town_hall = next((b for b in buildings if b.type_tag == "TOWN_HALL"), None)
    if town_hall is None or not hasattr(town_hall, "warehouse_amount"):
        return []
    available = int(town_hall.warehouse_amount("wood"))
    if available <= 0:
        return []
    tasks: list[TransportTask] = []
    remaining_wood = available
    for building in buildings:
        if building.type_tag != "SAWMILL":
            continue
        if getattr(building, "is_under_construction", False):
            continue
        if not getattr(building, "active", False):
            continue
        want = max(0, int(getattr(building, "input_capacity", lambda: 0)()) - int(getattr(building, "input_amount", lambda: 0)()))
        if want <= 0:
            continue
        count = min(want, remaining_wood)
        for _ in range(count):
            tasks.append(TransportTask(resource="wood", source=town_hall, target=building, priority=0))
        remaining_wood -= count
        if remaining_wood <= 0:
            break
    return tasks


def sawmill_output_transport_tasks(registry: Any) -> list[TransportTask]:
    """Build low-priority export tasks from sawmills to Town Hall warehouse."""
    if registry is None:
        return []
    buildings = list(registry.all())
    town_hall = next((b for b in buildings if b.type_tag == "TOWN_HALL"), None)
    if town_hall is None:
        return []
    tasks: list[TransportTask] = []
    for building in buildings:
        if building.type_tag != "SAWMILL":
            continue
        if getattr(building, "is_under_construction", False):
            continue
        amount = int(getattr(building, "output_amount", lambda: 0)())
        if amount <= 0:
            continue
        for _ in range(amount):
            tasks.append(TransportTask(resource="boards", source=building, target=town_hall, priority=0))
    return tasks


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
        "transport_task",
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
        self.transport_task: TransportTask | None = None

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
            elif move_state == "going_to_plant_tile":
                self.state = "going_to_plant_tile"
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
        if self.state not in {"moving", "going_to_tree", "going_to_stone", "going_to_plant_tile", "returning"} or self.target_tile is None:
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
            elif self.state == "going_to_plant_tile":
                self.state = "arrived_plant_tile"
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

    __slots__ = ("_now_ms_fn", "_registry", "_workers", "_transport_queue", "_updaters")
    _WORKER_TO_BUILDING: dict[str, str] = {
        "LUMBERJACK": "LUMBER_CAMP",
        "STONECUTTER": "STONE_MINE",
        "MINER": "IRON_MINE",
        "FARMER": "FARM",
        "FORESTER": "FORESTER_HUT",
        "SAWYER": "SAWMILL",
    }
    _HIRABLE_WORKERS: set[str] = set(_WORKER_TO_BUILDING) | {"CARRIER", "BUILDER"}

    def __init__(
        self,
        registry: Any | None = None,
        *,
        now_ms_fn: Callable[[], int] | None = None,
    ) -> None:
        self._registry = registry
        self._workers: list[Worker] = []
        self._transport_queue: list[TransportTask] = []
        self._now_ms_fn = now_ms_fn or (lambda: 0)
        self._updaters: dict[str, Callable[[Worker, int, Any], None]] = {
            "FORESTER": self._update_forester,
            "CARRIER": self._update_carrier,
            "LUMBERJACK": self._update_gatherer,
            "STONECUTTER": self._update_gatherer,
            "BUILDER": self._update_builder,
            "SAWYER": self._update_sawyer,
        }
        if registry is not None and hasattr(registry, "bind_worker_manager"):
            registry.bind_worker_manager(self)

    def add_worker(self, worker: Worker) -> None:
        self._workers.append(worker)

    def bootstrap_starting_workers_near_town_hall(self, town_hall: Building) -> None:
        """Place two carriers and one builder on tiles directly below the Town Hall (visible, not under sprite)."""
        if self._registry is None or town_hall.type_tag != "TOWN_HALL":
            return
        t0, t1, t2 = self._starter_stand_tiles_near_town_hall(town_hall)
        self.add_worker(Worker("CARRIER", stand_tile=t0))
        self.add_worker(Worker("CARRIER", stand_tile=t1))
        self.add_worker(Worker("BUILDER", stand_tile=t2))

    def _starter_stand_tiles_near_town_hall(self, town_hall: Building) -> tuple[tuple[int, int], tuple[int, int], tuple[int, int]]:
        """Three stand tiles on the row immediately south of the footprint (center first, then sideways)."""
        preferred = town_hall_spawn_tile(town_hall)
        pos = town_hall.grid_pos
        if pos is None:
            return preferred, preferred, preferred
        gx, gy = pos
        _, h = type(town_hall).footprint
        south_row_y = gy + h
        below = [t for t in self._approach_tiles(town_hall) if t[1] == south_row_y]
        cx = preferred[0]
        below.sort(key=lambda t: (abs(t[0] - cx), t[0]))
        ordered = list(below)
        if not ordered:
            ordered = [preferred]
        while len(ordered) < 3:
            ordered.append(ordered[-1])
        return ordered[0], ordered[1], ordered[2]

    def workers(self) -> tuple[Worker, ...]:
        return tuple(self._workers)

    def enqueue_transport_task(
        self,
        *,
        resource: str,
        source: Building,
        target: Building,
        amount: int = 1,
        priority: int = 0,
    ) -> None:
        n = max(0, int(amount))
        for _ in range(n):
            self._transport_queue.append(
                TransportTask(
                    resource=str(resource),
                    source=source,
                    target=target,
                    priority=int(priority),
                )
            )

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
        if building.is_under_construction:
            for worker in self._workers:
                if worker.assigned_building is building:
                    return "resting"
            return "empty"
        for worker in self._workers:
            if worker.assigned_building is not building:
                continue
            if worker.type_tag == "FORESTER":
                if worker.state == "moving":
                    return "on the way"
                if worker.state == "going_to_plant_tile":
                    return "going to plant"
                if worker.state in {"arrived_plant_tile", "planting"}:
                    return "planting"
                if worker.state in {"returning", "arrived_camp"}:
                    return "returning"
                if worker.state == "return_path_blocked":
                    return "path blocked"
                if worker.state == "working":
                    now_ms = int(self._now_ms_fn())
                    if worker.camp_wait_until_ms > now_ms:
                        return "resting"
                    return "ready"
                if worker.state == "idle":
                    return "idle"
                return "assigned"
            if worker.state in {"moving", "going_to_tree", "going_to_stone", "going_to_plant_tile", "returning"}:
                return "on the way"
            return "assigned"
        return "empty"

    def production_status_for_building(self, building: Building) -> str:
        """Human-readable production status for building panels."""
        if building.is_under_construction:
            return "Under construction"
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

        moving_states = {"moving", "going_to_tree", "going_to_stone", "going_to_plant_tile", "returning"}
        if worker.state in moving_states:
            return "On the way"
        if worker.state in {"chopping", "mining", "planting"}:
            return "Gathering"
        if worker.state == "depositing":
            return "Depositing"
        if worker.state in {"arrived_tree", "arrived_stone", "arrived_plant_tile"}:
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

    def hire(
        self,
        worker_type: str,
        *,
        source_building: Building | None = None,
        charge_cost: bool = True,
    ) -> Worker | None:
        """Hire a worker if town hall level and housing allow it."""
        if self._registry is None:
            return None
        if worker_type not in self._HIRABLE_WORKERS:
            return None
        if not self._has_housing_capacity_for(incoming=1):
            return None
        min_level = int(TOWN_HALL_MIN_LEVEL_FOR_HIRE.get(worker_type, 1))
        th_level = 0
        for b in self._registry.all():
            if b.type_tag == "TOWN_HALL":
                th_level = b.level
                break
        if th_level < min_level:
            return None
        _ = charge_cost
        spawn_anchor = source_building
        all_buildings = self._registry.all()
        if spawn_anchor not in all_buildings:
            spawn_anchor = None
        if spawn_anchor is None:
            schools = [b for b in all_buildings if b.type_tag == "SCHOOL"]
            if schools:
                # Hiring is centralized in School; if caller did not pass explicit source,
                # prefer the latest placed school over Town Hall legacy spawn.
                spawn_anchor = schools[-1]
            else:
                spawn_anchor = next((b for b in all_buildings if b.type_tag == "TOWN_HALL"), None)
        stand = (17, 19)
        if spawn_anchor is not None:
            if spawn_anchor.type_tag == "TOWN_HALL":
                stand = town_hall_spawn_tile(spawn_anchor)
            else:
                pos = spawn_anchor.grid_pos
                if pos is None:
                    stand = building_center_tile(spawn_anchor)
                else:
                    gx, gy = pos
                    w, h = type(spawn_anchor).footprint
                    # For School hiring, spawn at the tile below the building center.
                    stand = (gx + w // 2, gy + h)
            world = getattr(self._registry, "_world", None)
            if world is not None and (
                not world.is_in_grass(*stand) or world.is_occupied(*stand)
            ):
                approaches = self._approach_tiles(spawn_anchor)
                if approaches:
                    stand = approaches[0]
                else:
                    stand = building_center_tile(spawn_anchor)
        worker = Worker(worker_type, stand_tile=stand)
        self._workers.append(worker)
        return worker

    def can_hire(self, worker_type: str, *, charge_cost: bool = True) -> bool:
        """Whether current state allows hiring this worker type."""
        if self._registry is None:
            return False
        if worker_type not in self._HIRABLE_WORKERS:
            return False
        if not self._has_housing_capacity_for(incoming=1):
            return False
        min_level = int(TOWN_HALL_MIN_LEVEL_FOR_HIRE.get(worker_type, 1))
        th_level = 0
        for b in self._registry.all():
            if b.type_tag == "TOWN_HALL":
                th_level = b.level
                break
        _ = charge_cost
        return th_level >= min_level

    def _has_housing_capacity_for(self, *, incoming: int) -> bool:
        if self._registry is None:
            return True
        cap = max_population(self._registry, self)
        pop_now = current_population(self._registry, self)
        return pop_now + int(incoming) <= cap

    def notify_demolished(self, building: Building) -> None:
        """Workers targeting this building become idle at their current tile."""
        world = getattr(self._registry, "_world", None) if self._registry is not None else None
        site = building.construction_site
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
            if site is not None:
                if site.builder is w:
                    site.builder = None
                if site.resting_worker is w:
                    site.resting_worker = None

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
                and not worker.assigned_building.is_under_construction
            ):
                camp = worker.assigned_building
                self._park_worker_inside_camp(worker, camp)
                rest_ms = LUMBERJACK_REST_MS if worker.type_tag == "LUMBERJACK" else STONECUTTER_REST_MS
                worker.camp_wait_until_ms = max(worker.camp_wait_until_ms, now_ms + rest_ms)
                continue
            targets = [b for b in self._registry.all() if b.type_tag == want and not self.is_staffed(b) and not b.is_under_construction]
            targets.sort(
                key=lambda b: (
                    abs(worker.current_tile[0] - building_center_tile(b)[0])
                    + abs(worker.current_tile[1] - building_center_tile(b)[1])
                )
            )
            assigned = False
            blocked = world.blocked_tiles()
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
        blocked = world.blocked_tiles()
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
                if (x, y) in blocked:
                    continue
                tiles.append((x, y))
        return tiles

    def update(self, now_ms: int) -> None:
        """Advance worker movement interpolation/state for this frame."""
        world = getattr(self._registry, "_world", None) if self._registry is not None else None
        self._enqueue_construction_transport_tasks()
        self._enqueue_sawmill_refill_tasks()
        self._enqueue_sawmill_output_tasks()
        completed_buildings: list[Building] = []
        completed_site_builders: dict[int, Worker] = {}
        for worker in self._workers:
            worker.update(now_ms)
            updater = self._updaters.get(worker.type_tag)
            if updater is not None:
                updater(worker, int(now_ms), world)
        spawned = False
        if self._registry is not None:
            for building in self._registry.all():
                if not building.is_under_construction:
                    continue
                site = building.construction_site
                if site is None or not site.is_building():
                    continue
                if site.builder is not None:
                    completed_site_builders[id(building)] = site.builder
                if complete_construction(building, int(now_ms)):
                    completed_buildings.append(building)
            for building in completed_buildings:
                builder = completed_site_builders.get(id(building))
                if builder is not None:
                    self._move_worker_to_building_approach(builder, building)
                self.refresh_building_bonuses(building)
            if completed_buildings:
                self.reassign_all()
            for building in self._registry.all():
                if not isinstance(building, School):
                    continue
                trained_type = building.update_training(int(now_ms))
                if trained_type is None:
                    continue
                if self.hire(trained_type, source_building=building, charge_cost=False) is not None:
                    spawned = True
            if spawned:
                self.reassign_all()

    def _update_gatherer(self, worker: Worker, now_ms: int, world: Any) -> None:
        if world is None:
            return
        camp = worker.assigned_building
        if camp is None:
            world.release_reservations_for(worker)
            return
        # Under-construction buildings must not run production cycles.
        if camp.is_under_construction:
            return

        gather_state = self._gather_state_for(worker.type_tag)
        if gather_state is None:
            return

        # Gather worker just walked into the camp: kick off the cycle from the
        # actual arrival timestamp so leftover time in this tick still moves the
        # worker further along the new (resource-targeting) path.
        if worker.state == "working":
            self._park_worker_inside_camp(worker, camp)
            if worker.camp_wait_until_ms <= 0:
                worker.camp_wait_until_ms = worker.arrival_ms + gather_state["rest_ms"]
            if now_ms < worker.camp_wait_until_ms:
                return
            if not getattr(camp, "active", False):
                return
            if hasattr(camp, "is_storage_full") and camp.is_storage_full():
                # Keep waiting inside the camp while storage is full.
                worker.camp_wait_until_ms = now_ms + 1_000
                return
            depart_ms = worker.camp_wait_until_ms
            if not self._start_gather_cycle(worker, camp, depart_ms, world_query=gather_state["world_query"]):
                # No target/path right now: stay inside camp and retry later.
                self._park_worker_inside_camp(worker, camp)
                worker.camp_wait_until_ms = now_ms + 1_000
                return
            worker.camp_wait_until_ms = 0
            worker.update(now_ms)

        if worker.state == gather_state["arrived_state"]:
            worker.state = gather_state["work_state"]
            worker.chop_started_ms = now_ms
            speed = worker.characteristics.gather_speed_mult
            if speed <= 0.0:
                worker.chop_duration_ms = gather_state["duration_ms"]
            else:
                worker.chop_duration_ms = max(1, int(round(gather_state["duration_ms"] / speed)))
            return

        if worker.state == gather_state["work_state"]:
            if now_ms - worker.chop_started_ms < worker.chop_duration_ms:
                return
            target_tile = worker.target_tree
            if target_tile is not None:
                if gather_state["world_query"] == "tree":
                    world.remove_tree(*target_tile)
                else:
                    world.harvest_stone(*target_tile)
            worker.carrying = gather_state["carry_resource"]
            if not self._start_return_to_camp(worker, now_ms):
                worker.state = "depositing"
            return

        if worker.state == "arrived_camp":
            self._park_worker_inside_camp(worker, camp)
            worker.state = "depositing"
            return

        if worker.state == "depositing":
            if worker.carrying == gather_state["carry_resource"]:
                if hasattr(camp, "add_to_storage"):
                    camp.add_to_storage(1)
                resource = gather_state["carry_resource"]
                target = self._construction_target_for_resource(resource)
                priority = 10
                if target is None:
                    target = self._primary_town_hall()
                    priority = 0
                if target is not None:
                    self.enqueue_transport_task(
                        resource=resource,
                        source=camp,
                        target=target,
                        amount=1,
                        priority=priority,
                    )
                if hasattr(camp, gather_state["record_method"]):
                    record_method = getattr(camp, gather_state["record_method"])
                    record_method(1)
            worker.carrying = None
            worker.target_tree = None
            worker.chop_started_ms = 0
            worker.chop_duration_ms = CHOP_DURATION_MS
            self._park_worker_inside_camp(worker, camp)
            worker.camp_wait_until_ms = now_ms + gather_state["rest_ms"]
            return

    def _primary_town_hall(self) -> TownHall | None:
        if self._registry is None:
            return None
        for building in self._registry.all():
            if isinstance(building, TownHall):
                return building
        return None

    def _construction_target_for_resource(self, resource: str) -> Building | None:
        if self._registry is None:
            return None
        key = str(resource).lower()
        for building in self._registry.all():
            if not building.is_under_construction:
                continue
            site = building.construction_site
            if site is None:
                continue
            if int(site.remaining_resources().get(key, 0)) > 0:
                return building
        return None

    def _next_transport_task(self) -> TransportTask | None:
        if self._registry is None:
            return None
        known = set(self._registry.all())
        eligible: list[tuple[int, TransportTask]] = []
        for idx, task in enumerate(self._transport_queue):
            if task.source not in known or task.target not in known:
                continue
            has_storage_source = False
            if hasattr(task.source, "stored") and int(getattr(task.source, "stored", 0)) > 0:
                has_storage_source = True
            elif task.resource == "wood" and hasattr(task.source, "input_amount"):
                has_storage_source = int(task.source.input_amount()) > 0  # type: ignore[attr-defined]
            elif task.resource == "boards" and hasattr(task.source, "output_amount"):
                has_storage_source = int(task.source.output_amount()) > 0  # type: ignore[attr-defined]
            has_warehouse_source = hasattr(task.source, "warehouse_amount") and int(
                task.source.warehouse_amount(task.resource)  # type: ignore[attr-defined]
            ) > 0
            if not has_storage_source and not has_warehouse_source:
                continue
            eligible.append((idx, task))
        if not eligible:
            return None
        best_idx, _ = max(eligible, key=lambda item: (int(item[1].priority), -item[0]))
        return self._transport_queue.pop(best_idx)

    def _start_move_to_building(self, worker: Worker, building: Building, now_ms: int) -> bool:
        if self._registry is None:
            return False
        world = getattr(self._registry, "_world", None)
        if world is None:
            return False
        blocked = world.blocked_tiles()
        blocked.discard(worker.current_tile)
        best_path: list[tuple[int, int]] | None = None
        for tile in self._approach_tiles(building):
            path = find_path_bfs(world, worker.current_tile, tile, blocked)
            if path is None:
                continue
            if best_path is None or len(path) < len(best_path):
                best_path = path
        if best_path is None:
            return False
        worker.start_move(best_path, started_ms=now_ms)
        return True

    def _update_carrier(self, worker: Worker, now_ms: int, world: Any) -> None:
        if self._registry is None or world is None:
            return
        task = worker.transport_task
        if task is None:
            if worker.state != "idle":
                worker.state = "idle"
                worker.idle = True
            task = self._next_transport_task()
            if task is None:
                return
            worker.transport_task = task
            worker.carrying = None
            if not self._start_move_to_building(worker, task.source, now_ms):
                self._transport_queue.insert(0, task)
                worker.transport_task = None
                worker.state = "idle"
                worker.idle = True
            return

        if worker.state in {"moving", "returning"}:
            return

        if worker.carrying is None:
            if worker.state != "carrier_loading":
                self._park_worker_inside_building(worker, task.source)
                worker.state = "carrier_loading"
                worker.camp_wait_until_ms = now_ms + CARRIER_INTERACT_MS
                return
            if now_ms < worker.camp_wait_until_ms:
                return
            if task.source not in self._registry.all() or task.target not in self._registry.all():
                worker.transport_task = None
                worker.state = "idle"
                worker.idle = True
                return
            if not hasattr(task.source, "take_from_storage"):
                if task.resource == "wood" and hasattr(task.source, "take_wood_in"):
                    try:
                        task.source.take_wood_in(1)  # type: ignore[attr-defined]
                    except ValueError:
                        self._transport_queue.append(task)
                        worker.transport_task = None
                        worker.state = "idle"
                        worker.idle = True
                        next_task = self._next_transport_task()
                        if next_task is not None:
                            worker.transport_task = next_task
                            worker.carrying = None
                            if not self._start_move_to_building(worker, next_task.source, now_ms):
                                self._transport_queue.insert(0, next_task)
                                worker.transport_task = None
                                worker.state = "idle"
                                worker.idle = True
                        return
                elif task.resource == "boards" and hasattr(task.source, "take_boards_out"):
                    try:
                        task.source.take_boards_out(1)  # type: ignore[attr-defined]
                    except ValueError:
                        self._transport_queue.append(task)
                        worker.transport_task = None
                        worker.state = "idle"
                        worker.idle = True
                        next_task = self._next_transport_task()
                        if next_task is not None:
                            worker.transport_task = next_task
                            worker.carrying = None
                            if not self._start_move_to_building(worker, next_task.source, now_ms):
                                self._transport_queue.insert(0, next_task)
                                worker.transport_task = None
                                worker.state = "idle"
                                worker.idle = True
                        return
                elif not hasattr(task.source, "take_from_warehouse"):
                    worker.transport_task = None
                    worker.state = "idle"
                    worker.idle = True
                    return
                else:
                    try:
                        task.source.take_from_warehouse(task.resource, 1)  # type: ignore[attr-defined]
                    except ValueError:
                        self._transport_queue.append(task)
                        worker.transport_task = None
                        worker.state = "idle"
                        worker.idle = True
                        next_task = self._next_transport_task()
                        if next_task is not None:
                            worker.transport_task = next_task
                            worker.carrying = None
                            if not self._start_move_to_building(worker, next_task.source, now_ms):
                                self._transport_queue.insert(0, next_task)
                                worker.transport_task = None
                                worker.state = "idle"
                                worker.idle = True
                        return
            else:
                try:
                    task.source.take_from_storage(1)  # type: ignore[attr-defined]
                except ValueError:
                    self._transport_queue.append(task)
                    worker.transport_task = None
                    worker.state = "idle"
                    worker.idle = True
                    next_task = self._next_transport_task()
                    if next_task is not None:
                        worker.transport_task = next_task
                        worker.carrying = None
                        if not self._start_move_to_building(worker, next_task.source, now_ms):
                            self._transport_queue.insert(0, next_task)
                            worker.transport_task = None
                            worker.state = "idle"
                            worker.idle = True
                    return
            worker.carrying = task.resource
            if isinstance(task.source, TownHall):
                # Town Hall center can trap pathfinding because it is fully enclosed by occupied tiles.
                self._move_worker_to_building_approach(worker, task.source)
            if not self._start_move_to_building(worker, task.target, now_ms):
                if task.resource == "wood" and hasattr(task.source, "add_wood_in"):
                    task.source.add_wood_in(1)  # type: ignore[attr-defined]
                elif task.resource == "boards" and hasattr(task.source, "add_boards_out"):
                    task.source.add_boards_out(1)  # type: ignore[attr-defined]
                elif hasattr(task.source, "add_to_storage"):
                    task.source.add_to_storage(1)  # type: ignore[attr-defined]
                elif hasattr(task.source, "add_to_warehouse"):
                    task.source.add_to_warehouse(task.resource, 1)  # type: ignore[attr-defined]
                worker.carrying = None
                self._transport_queue.insert(0, task)
                worker.transport_task = None
                worker.state = "idle"
                worker.idle = True
            return

        if worker.state != "carrier_unloading":
            self._park_worker_inside_building(worker, task.target)
            worker.state = "carrier_unloading"
            worker.camp_wait_until_ms = now_ms + CARRIER_INTERACT_MS
            return
        if now_ms < worker.camp_wait_until_ms:
            return
        delivered_target = task.target
        site = task.target.construction_site if task.target.is_under_construction else None
        if site is not None:
            remaining = int(site.remaining_resources().get(str(task.resource).lower(), 0))
            if remaining > 0:
                site.deliver_resource(task.resource, 1)
            else:
                town_hall = self._primary_town_hall()
                if town_hall is not None:
                    town_hall.add_to_warehouse(task.resource, 1)
                    delivered_target = town_hall
                elif hasattr(task.target, "add_to_warehouse"):
                    task.target.add_to_warehouse(task.resource, 1)  # type: ignore[attr-defined]
        elif task.resource == "wood" and hasattr(task.target, "add_wood_in"):
            if int(task.target.input_amount()) < int(task.target.input_capacity()):  # type: ignore[attr-defined]
                task.target.add_wood_in(1)  # type: ignore[attr-defined]
            else:
                town_hall = self._primary_town_hall()
                if town_hall is not None:
                    town_hall.add_to_warehouse(task.resource, 1)
                    delivered_target = town_hall
                elif hasattr(task.target, "add_to_warehouse"):
                    task.target.add_to_warehouse(task.resource, 1)  # type: ignore[attr-defined]
        elif task.resource == "boards" and hasattr(task.target, "add_to_warehouse"):
            task.target.add_to_warehouse(task.resource, 1)  # type: ignore[attr-defined]
        elif hasattr(task.target, "add_to_warehouse"):
            task.target.add_to_warehouse(task.resource, 1)  # type: ignore[attr-defined]
        self._move_worker_to_building_approach(worker, delivered_target)
        worker.carrying = None
        worker.transport_task = None
        worker.state = "idle"
        worker.idle = True

    def _enqueue_construction_transport_tasks(self) -> None:
        if self._registry is None:
            return
        desired = construction_transport_tasks(self._registry)
        desired_counts: dict[tuple[int, int, str, int], int] = {}
        for task in desired:
            key = (id(task.source), id(task.target), task.resource, int(task.priority))
            desired_counts[key] = desired_counts.get(key, 0) + 1

        existing_counts: dict[tuple[int, int, str, int], int] = {}
        for task in self._transport_queue:
            key = (id(task.source), id(task.target), task.resource, int(task.priority))
            existing_counts[key] = existing_counts.get(key, 0) + 1
        for worker in self._workers:
            task = worker.transport_task
            if task is None:
                continue
            key = (id(task.source), id(task.target), task.resource, int(task.priority))
            existing_counts[key] = existing_counts.get(key, 0) + 1

        for task in desired:
            key = (id(task.source), id(task.target), task.resource, int(task.priority))
            if existing_counts.get(key, 0) >= desired_counts.get(key, 0):
                continue
            self.enqueue_transport_task(
                resource=task.resource,
                source=task.source,
                target=task.target,
                amount=1,
                priority=task.priority,
            )
            existing_counts[key] = existing_counts.get(key, 0) + 1

    def _enqueue_sawmill_refill_tasks(self) -> None:
        if self._registry is None:
            return
        desired = sawmill_input_transport_tasks(self._registry)
        desired_counts: dict[tuple[int, int, str, int], int] = {}
        for task in desired:
            key = (id(task.source), id(task.target), task.resource, int(task.priority))
            desired_counts[key] = desired_counts.get(key, 0) + 1

        existing_counts: dict[tuple[int, int, str, int], int] = {}
        for task in self._transport_queue:
            key = (id(task.source), id(task.target), task.resource, int(task.priority))
            existing_counts[key] = existing_counts.get(key, 0) + 1
        for worker in self._workers:
            task = worker.transport_task
            if task is None:
                continue
            key = (id(task.source), id(task.target), task.resource, int(task.priority))
            existing_counts[key] = existing_counts.get(key, 0) + 1

        for task in desired:
            key = (id(task.source), id(task.target), task.resource, int(task.priority))
            if existing_counts.get(key, 0) >= desired_counts.get(key, 0):
                continue
            self.enqueue_transport_task(
                resource=task.resource,
                source=task.source,
                target=task.target,
                amount=1,
                priority=task.priority,
            )
            existing_counts[key] = existing_counts.get(key, 0) + 1

    def _enqueue_sawmill_output_tasks(self) -> None:
        if self._registry is None:
            return
        desired = sawmill_output_transport_tasks(self._registry)
        desired_counts: dict[tuple[int, int, str, int], int] = {}
        for task in desired:
            key = (id(task.source), id(task.target), task.resource, int(task.priority))
            desired_counts[key] = desired_counts.get(key, 0) + 1

        existing_counts: dict[tuple[int, int, str, int], int] = {}
        for task in self._transport_queue:
            key = (id(task.source), id(task.target), task.resource, int(task.priority))
            existing_counts[key] = existing_counts.get(key, 0) + 1
        for worker in self._workers:
            task = worker.transport_task
            if task is None:
                continue
            key = (id(task.source), id(task.target), task.resource, int(task.priority))
            existing_counts[key] = existing_counts.get(key, 0) + 1

        for task in desired:
            key = (id(task.source), id(task.target), task.resource, int(task.priority))
            if existing_counts.get(key, 0) >= desired_counts.get(key, 0):
                continue
            self.enqueue_transport_task(
                resource=task.resource,
                source=task.source,
                target=task.target,
                amount=1,
                priority=task.priority,
            )
            existing_counts[key] = existing_counts.get(key, 0) + 1

    def _update_forester(self, worker: Worker, now_ms: int, world: Any) -> None:
        if world is None:
            return
        hut = worker.assigned_building
        if hut is None:
            world.release_reservations_for(worker)
            return
        # Under-construction huts must not run planting cycles.
        if hut.is_under_construction:
            return

        if worker.state == "working":
            self._park_forester_inside_hut(worker, hut)
            if not getattr(hut, "active", False):
                return
            if worker.camp_wait_until_ms <= 0:
                worker.camp_wait_until_ms = now_ms + FORESTER_REST_MS
            if now_ms < worker.camp_wait_until_ms:
                return
            # Start walking from "now" to preserve smooth interpolation.
            depart_ms = now_ms
            if not self._start_forester_cycle(worker, hut, depart_ms, world):
                worker.camp_wait_until_ms = now_ms + FORESTER_TARGET_RETRY_MS
                return
            worker.camp_wait_until_ms = 0
            return

        if worker.state == "arrived_plant_tile":
            worker.state = "planting"
            worker.chop_started_ms = now_ms
            worker.chop_duration_ms = PLANT_DURATION_MS
            return

        if worker.state == "planting":
            if now_ms - worker.chop_started_ms < worker.chop_duration_ms:
                return
            target_tile = worker.target_tile
            if target_tile is not None:
                world.plant_tree(*target_tile, now_ms=now_ms)
            if not self._start_return_to_camp(worker, now_ms):
                # Never teleport forester home: if path is temporarily unavailable,
                # stay on the current tile and retry pathing on next ticks.
                worker.state = "return_path_blocked"
                worker.camp_wait_until_ms = now_ms + FORESTER_RETURN_RETRY_MS
            return

        if worker.state == "return_path_blocked":
            if now_ms < worker.camp_wait_until_ms:
                return
            if self._start_return_to_camp(worker, now_ms):
                worker.camp_wait_until_ms = 0
                return
            worker.camp_wait_until_ms = now_ms + FORESTER_RETURN_RETRY_MS
            return

        if worker.state == "arrived_camp":
            self._park_forester_inside_hut(worker, hut)
            worker.target_tile = None
            worker.chop_started_ms = 0
            worker.chop_duration_ms = CHOP_DURATION_MS
            worker.camp_wait_until_ms = now_ms + FORESTER_REST_MS
            return
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

    def _start_forester_cycle(self, worker: Worker, hut: Building, now_ms: int, world: Any) -> bool:
        target_tile = self._select_forester_target(world, hut, worker.current_tile)
        if target_tile is None:
            return False
        blocked = world.blocked_tiles()
        blocked.discard(worker.current_tile)
        path = find_path_bfs(world, worker.current_tile, target_tile, blocked)
        if path is None:
            return False
        worker.target_tile = target_tile
        worker.start_move(path, started_ms=now_ms, move_state="going_to_plant_tile")

    def _update_builder(self, worker: Worker, now_ms: int, world: Any) -> None:
        if world is None or self._registry is None:
            return
        building = worker.assigned_building
        if building is not None:
            site = building.construction_site
            if site is None or not building.is_under_construction:
                worker.assigned_building = None
                worker.idle = True
                worker.state = "idle"
                return
            if site.builder is worker:
                worker.idle = False
                worker.state = "building"
                return
            if site.builder is not None or not site.is_fully_supplied():
                worker.assigned_building = None
                worker.idle = True
                worker.state = "idle"
                return
            if worker.state == "moving":
                return
            worker.state = "entering_site"
            self._park_worker_inside_building(worker, building)
            site.builder = worker
            site.build_started_ms = int(now_ms)
            worker.state = "building"
            return

        if not worker.idle:
            return
        targets = [
            b
            for b in self._registry.all()
            if b.is_under_construction
            and b.construction_site is not None
            and b.construction_site.is_fully_supplied()
            and b.construction_site.builder is None
        ]
        targets.sort(
            key=lambda b: (
                abs(worker.current_tile[0] - building_center_tile(b)[0])
                + abs(worker.current_tile[1] - building_center_tile(b)[1])
            )
        )
        blocked = world.blocked_tiles()
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
            return
        return True

    @staticmethod
    def _sawmill_cycle_duration_ms(sawmill: Any) -> int:
        level = max(1, int(getattr(sawmill, "level", 1)))
        mult = 1.0 - 0.02 * float(level - 1)
        effective = int(round(SAWMILL_BASE_CYCLE_MS * mult))
        return max(SAWMILL_MIN_CYCLE_MS, effective)

    @staticmethod
    def _update_sawyer(worker: Worker, now_ms: int, world: Any) -> None:
        _ = world
        sawmill = worker.assigned_building
        if sawmill is None or sawmill.type_tag != "SAWMILL":
            return
        if sawmill.is_under_construction:
            return
        active = bool(getattr(sawmill, "active", False))
        if worker.state == "resting":
            if now_ms < worker.camp_wait_until_ms:
                return
            worker.state = "working"
            worker.camp_wait_until_ms = 0
            worker.idle = False
        if worker.state == "resting":
            return
        if worker.state == "processing":
            started = int(getattr(sawmill, "processing_started_ms", 0))
            if started <= 0:
                worker.state = "working"
                return
            duration = WorkerManager._sawmill_cycle_duration_ms(sawmill)
            sawmill.processing_duration_ms = duration
            if now_ms - started < duration:
                return
            if getattr(sawmill, "input_amount", lambda: 0)() > 0 and getattr(
                sawmill, "output_amount", lambda: 0
            )() < getattr(sawmill, "output_capacity", lambda: 0)():
                sawmill.take_wood_in(1)
                sawmill.add_boards_out(1)
            sawmill.processing_started_ms = 0
            worker.state = "resting"
            worker.camp_wait_until_ms = int(now_ms) + SAWYER_REST_MS
            worker.idle = False
            return
        if not active:
            return
        if getattr(sawmill, "input_amount", lambda: 0)() <= 0:
            return
        if getattr(sawmill, "output_amount", lambda: 0)() >= getattr(sawmill, "output_capacity", lambda: 0)():
            return
        if worker.state != "working":
            return
        if int(getattr(sawmill, "processing_started_ms", 0)) <= 0:
            sawmill.processing_started_ms = int(now_ms)
        sawmill.processing_duration_ms = WorkerManager._sawmill_cycle_duration_ms(sawmill)
        worker.state = "processing"
        worker.idle = False

    @staticmethod
    def _select_forester_target(
        world: Any, hut: Building, from_tile: tuple[int, int]
    ) -> tuple[int, int] | None:
        hx, hy = building_center_tile(hut)
        blocked = world.blocked_tiles()
        blocked.discard(from_tile)
        pos = hut.grid_pos
        if pos is None:
            return None
        gx, gy = pos
        w, h = type(hut).footprint
        hut_approaches: list[tuple[int, int]] = []
        for ay in range(gy - 1, gy + h + 1):
            for ax in range(gx - 1, gx + w + 1):
                inside = gx <= ax < gx + w and gy <= ay < gy + h
                if inside:
                    continue
                if not world.is_in_grass(ax, ay):
                    continue
                if (ax, ay) in blocked:
                    continue
                hut_approaches.append((ax, ay))
        if not hut_approaches:
            return None
        approach_set = set(hut_approaches)
        for _ in range(FORESTER_TARGET_RANDOM_TRIES):
            x = random.randint(hx - 15, hx + 15)
            y = random.randint(hy - 15, hy + 15)
            if not world.is_in_grass(x, y):
                continue
            if (x, y) == from_tile:
                continue
            if (x, y) in approach_set:
                continue
            if (x, y) in blocked:
                continue
            if world.is_occupied(x, y) or world.is_tree_blocking(x, y) or world.is_stone_blocking(x, y):
                continue
            near_building = False
            for ny in range(y - 1, y + 2):
                for nx in range(x - 1, x + 2):
                    if world.is_occupied(nx, ny):
                        near_building = True
                        break
                if near_building:
                    break
            if near_building:
                continue
            path = find_path_bfs(world, from_tile, (x, y), blocked)
            if path is None:
                continue
            return (x, y)
        return None

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
        blocked = world.blocked_tiles()
        blocked.discard(worker.current_tile)
        rejected_targets: set[tuple[int, int]] = set()
        while True:
            target_tile = self._find_nearest_gather_target(
                world,
                worker.current_tile,
                camp=camp,
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
        camp: Building,
        blocked: set[tuple[int, int]],
        world_query: str,
        skip_targets: set[tuple[int, int]] | None = None,
    ) -> tuple[int, int] | None:
        anchor = building_center_tile(camp)
        radius = GATHER_RESOURCE_SEARCH_RADIUS
        if world_query == "tree":
            return find_nearest_free_tree(
                world,
                from_tile,
                blocked=blocked,
                skip_reserved=True,
                skip_targets=skip_targets,
                search_anchor=anchor,
                max_search_radius=radius,
            )
        if world_query == "stone":
            return find_nearest_free_stone(
                world,
                from_tile,
                blocked=blocked,
                skip_reserved=True,
                skip_targets=skip_targets,
                search_anchor=anchor,
                max_search_radius=radius,
            )
        return None

    def _start_return_to_camp(self, worker: Worker, now_ms: int) -> bool:
        if self._registry is None or worker.assigned_building is None:
            return False
        world = getattr(self._registry, "_world", None)
        if world is None:
            return False
        blocked = world.blocked_tiles()
        blocked.discard(worker.current_tile)
        # Forester plants a tree on its current tile; pathfinder forbids blocked start tiles.
        # Temporarily unmark that single tile while computing a route out, then restore it.
        restored_tree = None
        if worker.type_tag == "FORESTER":
            restored_tree = world.tree_at(*worker.current_tile)
            if restored_tree is not None:
                world._trees.pop(worker.current_tile, None)  # noqa: SLF001
        best_path: list[tuple[int, int]] | None = None
        try:
            for tile in self._approach_tiles(worker.assigned_building):
                path = find_path_bfs(world, worker.current_tile, tile, blocked)
                if path is None:
                    continue
                if best_path is None or len(path) < len(best_path):
                    best_path = path
        finally:
            if restored_tree is not None and world.tree_at(*worker.current_tile) is None:
                world._trees[worker.current_tile] = restored_tree  # noqa: SLF001
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
    def _park_forester_inside_hut(worker: Worker, hut: Building) -> None:
        """Forester is considered inside hut between cycles (not on approach tile)."""
        center = building_center_tile(hut)
        worker.current_tile = center
        worker.stand_tile = center
        worker.target_tile = None
        worker.path = []
        worker.segment_progress = 0.0
        worker.idle = False
        worker.state = "working"

    @staticmethod
    def _park_worker_inside_building(worker: Worker, building: Building) -> None:
        center = building_center_tile(building)
        worker.current_tile = center
        worker.stand_tile = center
        worker.target_tile = None
        worker.path = []
        worker.segment_progress = 0.0
        worker.idle = False

    def _move_worker_to_building_approach(self, worker: Worker, building: Building) -> None:
        approach_tiles = self._approach_tiles(building)
        preferred_tile: tuple[int, int] | None = None
        if isinstance(building, TownHall) and building.grid_pos is not None:
            gx, gy = building.grid_pos
            w, h = type(building).footprint
            preferred_tile = (gx + w // 2, gy + h)  # always below Town Hall
        if approach_tiles:
            target = approach_tiles[0]
            if preferred_tile is not None and preferred_tile in approach_tiles:
                target = preferred_tile
            worker.current_tile = target
            worker.stand_tile = target
        else:
            center = building_center_tile(building)
            worker.current_tile = center
            worker.stand_tile = center
        worker.target_tile = worker.current_tile
        worker.path = []
        worker.segment_progress = 0.0

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
