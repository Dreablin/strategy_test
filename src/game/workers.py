"""Workers coordinator/facade.

New worker behavior belongs in focused worker modules; see
``worker_extension_guide.md`` before adding worker types or state machines.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from game.buildings.base import Building
from game.buildings.school import School
from game.construction import complete_construction
from game.pathfinding import find_path_bfs
from game.transport_tasks import (
    bakery_input_transport_tasks,
    bakery_output_transport_tasks,
    chicken_farm_output_transport_tasks,
    cow_farm_beef_output_transport_tasks,
    cow_farm_hide_output_transport_tasks,
    construction_transport_tasks,
    farm_wheat_output_transport_tasks,
    vineyard_farm_grape_output_transport_tasks,
    iron_mine_output_transport_tasks,
    mill_input_transport_tasks,
    mill_output_transport_tasks,
    processor_input_transport_tasks,
    sawmill_input_transport_tasks,
    sawmill_output_transport_tasks,
    water_input_transport_tasks,
)
from game.worker_constants import (
    CHOP_DURATION_MS,
    FARMER_FIELD_RADIUS,
    FORESTER_PLANT_RADIUS,
    IRON_MINE_CYCLE_MS,
    LUMBER_CAMP_RESOURCE_RADIUS,
    LUMBERJACK_REST_MS,
    MINER_REST_MS,
    MINE_DURATION_MS,
    STONE_MINE_RESOURCE_RADIUS,
    STONECUTTER_REST_MS,
)
from game.config import building_worker_effects
from game.worker_geometry import (
    building_center_tile,
    select_farmer_field_target,
    select_ripe_vineyard_target_tile,
    town_hall_spawn_tile,
)
from game.worker_hiring import (
    HIRABLE_WORKERS,
    WORKER_TO_BUILDING,
    can_hire,
    has_housing_capacity_for,
    hire,
    worker_compatible_building_types,
)
from game.worker_models import TransportTask, Worker
from game.worker_satiety import apply_satiety_game_time
from game.worker_status import (
    production_status_for_building,
    worker_status_for_building,
)
from game.worker_building import WorkerBuildingMixin
from game.worker_farming import WorkerFarmingMixin
from game.worker_gathering import WorkerGatheringMixin
from game.worker_processing import WorkerProcessingMixin
from game.resource_catalog import is_simple_meal_resource
from game.worker_transport import WorkerTransportMixin
from game.world import find_nearest_free_stone, find_nearest_free_tree

__all__ = [
    "Worker",
    "WorkerManager",
    "TransportTask",
    "CHOP_DURATION_MS",
    "MINE_DURATION_MS",
    "IRON_MINE_CYCLE_MS",
    "MINER_REST_MS",
    "FARMER_FIELD_RADIUS",
    "FORESTER_PLANT_RADIUS",
    "LUMBER_CAMP_RESOURCE_RADIUS",
    "STONE_MINE_RESOURCE_RADIUS",
    "building_center_tile",
    "town_hall_spawn_tile",
    "select_farmer_field_target",
    "select_ripe_vineyard_target_tile",
    "construction_transport_tasks",
    "sawmill_input_transport_tasks",
    "sawmill_output_transport_tasks",
    "mill_input_transport_tasks",
    "mill_output_transport_tasks",
    "bakery_input_transport_tasks",
    "bakery_output_transport_tasks",
    "chicken_farm_output_transport_tasks",
    "cow_farm_beef_output_transport_tasks",
    "cow_farm_hide_output_transport_tasks",
    "iron_mine_output_transport_tasks",
    "farm_wheat_output_transport_tasks",
    "vineyard_farm_grape_output_transport_tasks",
    "processor_input_transport_tasks",
    "water_input_transport_tasks",
    "find_nearest_free_tree",
    "find_nearest_free_stone",
]


class WorkerManager(
    WorkerBuildingMixin,
    WorkerFarmingMixin,
    WorkerGatheringMixin,
    WorkerProcessingMixin,
    WorkerTransportMixin,
):
    """Tracks workers; notifies assignments when a staffed building is demolished (PRD F-WORK)."""

    __slots__ = (
        "_field_reservations",
        "_vineyard_plot_reservations",
        "_now_ms_fn",
        "_registry",
        "_transport_queue",
        "_updaters",
        "_workers",
    )
    _WORKER_TO_BUILDING: dict[str, str] = WORKER_TO_BUILDING
    _HIRABLE_WORKERS: set[str] = HIRABLE_WORKERS

    def __init__(
        self,
        registry: Any | None = None,
        *,
        now_ms_fn: Callable[[], int] | None = None,
    ) -> None:
        self._registry = registry
        self._workers: list[Worker] = []
        self._transport_queue: list[TransportTask] = []
        self._field_reservations: dict[tuple[int, int], Worker] = {}
        self._vineyard_plot_reservations: dict[tuple[int, int], Worker] = {}
        self._now_ms_fn = now_ms_fn or (lambda: 0)
        self._updaters: dict[str, Callable[[Worker, int, Any], None]] = {
            "FORESTER": self._update_forester,
            "CARRIER": self._update_carrier,
            "LUMBERJACK": self._update_gatherer,
            "STONECUTTER": self._update_gatherer,
            "MINER": self._update_miner,
            "BUILDER": self._update_builder,
            "SAWYER": self._update_sawyer,
            "MILLER": self._update_miller,
            "BAKER": self._update_baker,
            "COOK": self._update_cook,
            "WATERMAN": self._update_waterman,
            "ANIMAL_HERDER": self._update_animal_herder,
            "FARMER": self._update_farmer,
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

    def transport_queue_size(self) -> int:
        """Number of pending delivery tasks waiting for a carrier."""
        return len(self._transport_queue)

    def active_transport_count(self) -> int:
        """Number of delivery tasks currently assigned to carriers."""
        return sum(1 for worker in self._workers if worker.transport_task is not None)

    def enqueue_transport_task(
        self,
        *,
        resource: str,
        source: Building,
        target: Building,
        amount: int = 1,
        priority: int = 0,
        purpose: str = "generic",
    ) -> None:
        n = max(0, int(amount))
        if is_simple_meal_resource(resource) and getattr(target, "type_tag", "") == "TOWN_HALL":
            return
        task_purpose = str(purpose)
        if (
            task_purpose == "generic"
            and int(priority) >= 10
            and bool(getattr(target, "is_under_construction", False))
            and getattr(target, "construction_site", None) is not None
        ):
            task_purpose = "construction"
        for _ in range(n):
            self._transport_queue.append(
                TransportTask(
                    resource=str(resource),
                    source=source,
                    target=target,
                    priority=int(priority),
                    purpose=task_purpose,
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
        worker.blocked_cycle_hunger_try_ms = -1
        self._apply_building_bonus(worker, building)

    def is_staffed(self, building: Building) -> bool:
        return any(w.assigned_building is building for w in self._workers)

    def worker_status_for_building(self, building: Building) -> str:
        return worker_status_for_building(self, building)

    def production_status_for_building(self, building: Building) -> str:
        return production_status_for_building(self, building)

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
        return hire(
            self,
            worker_type,
            source_building=source_building,
            charge_cost=charge_cost,
        )

    def can_hire(self, worker_type: str, *, charge_cost: bool = True) -> bool:
        return can_hire(self, worker_type, charge_cost=charge_cost)

    def _has_housing_capacity_for(self, *, incoming: int) -> bool:
        return has_housing_capacity_for(self, incoming=incoming)

    def notify_demolished(self, building: Building) -> None:
        """Workers targeting this building become idle at their current tile."""
        world = getattr(self._registry, "_world", None) if self._registry is not None else None
        site = building.construction_site
        for w in self._workers:
            if w.assigned_building is building:
                if world is not None:
                    world.release_reservations_for(w)
                self._release_field_reservations_for(w)
                self._release_vineyard_plot_reservations_for(w)
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
                w.blocked_cycle_hunger_try_ms = -1
            if site is not None:
                if site.builder is w:
                    site.builder = None
                if site.resting_worker is w:
                    site.resting_worker = None
        if self._transport_queue:
            self._transport_queue = [
                t for t in self._transport_queue if t.source is not building and t.target is not building
            ]
        if building.type_tag == "FIELD" and building.grid_pos is not None:
            self._field_reservations.pop(tuple(building.grid_pos), None)
        if building.type_tag == "VINEYARD" and building.grid_pos is not None:
            gx, gy = int(building.grid_pos[0]), int(building.grid_pos[1])
            self._vineyard_plot_reservations.pop((gx, gy), None)

    def reassign_all(self) -> None:
        """Assign one idle worker per free matching building with path-to-approach."""
        if self._registry is None:
            return
        world = getattr(self._registry, "_world", None)
        if world is None:
            return
        now_ms = int(self._now_ms_fn())
        for worker in [w for w in self._workers if w.idle]:
            want_types = worker_compatible_building_types(worker.type_tag)
            if not want_types:
                continue
            # Gather worker already at its camp (e.g., post-deposit with toggle off, then on):
            # resume the gather cycle directly without walking back to the camp.
            if (
                worker.type_tag in {"LUMBERJACK", "STONECUTTER"}
                and worker.assigned_building is not None
                and worker.assigned_building.type_tag in want_types
                and not worker.assigned_building.is_under_construction
            ):
                camp = worker.assigned_building
                self._park_worker_inside_camp(worker, camp)
                rest_ms = LUMBERJACK_REST_MS if worker.type_tag == "LUMBERJACK" else STONECUTTER_REST_MS
                worker.camp_wait_until_ms = max(worker.camp_wait_until_ms, now_ms + rest_ms)
                continue
            targets = [
                b
                for b in self._registry.all()
                if b.type_tag in want_types and not self.is_staffed(b) and not b.is_under_construction
            ]
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

    def refresh_configured_worker_effects(self) -> None:
        """Recompute global and worker-type effects for all existing workers."""
        for worker in self._workers:
            worker.refresh_configured_effects()

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

    @staticmethod
    def _tick_worker_satiety(worker: Worker, now_ms: int) -> None:
        last = worker.satiety_last_sample_ms
        if last < 0:
            worker.satiety_last_sample_ms = int(now_ms)
            return
        worker.satiety, worker.satiety_last_sample_ms = apply_satiety_game_time(
            worker.satiety, last, now_ms
        )

    def _try_blocked_cycle_hunger(self, worker: Worker, now_ms: int) -> None:
        if self._registry is None:
            return
        world = getattr(self._registry, "_world", None)
        if world is None:
            return
        from game.worker_hunger import try_blocked_cycle_hunger_check

        try_blocked_cycle_hunger_check(
            worker,
            world=world,
            registry=self._registry,
            worker_manager=self,
            now_ms=int(now_ms),
        )

    def update(self, now_ms: int) -> None:
        """Advance worker movement interpolation/state for this frame."""
        world = getattr(self._registry, "_world", None) if self._registry is not None else None
        now_ms = int(now_ms)
        self._update_field_growth(int(now_ms))
        self._enqueue_construction_transport_tasks()
        self._enqueue_sawmill_refill_tasks()
        self._enqueue_sawmill_output_tasks()
        self._enqueue_mill_refill_tasks()
        self._enqueue_mill_output_tasks()
        self._enqueue_bakery_refill_tasks()
        self._enqueue_canteen_input_tasks()
        self._enqueue_water_input_tasks()
        self._enqueue_bakery_output_tasks()
        self._enqueue_chicken_farm_output_tasks()
        self._enqueue_cow_farm_beef_output_tasks()
        self._enqueue_cow_farm_hide_output_tasks()
        self._enqueue_iron_mine_output_tasks()
        self._enqueue_farm_wheat_output_tasks()
        self._enqueue_vineyard_farm_grape_output_tasks()
        if self._registry is not None:
            from game.buildings.canteen import Canteen
            from game.worker_dining import assign_diner_meals_for_canteen

            for building in self._registry.all():
                if isinstance(building, Canteen) and not building.is_under_construction:
                    assign_diner_meals_for_canteen(building, now_ms=now_ms)
        completed_buildings: list[Building] = []
        completed_site_builders: dict[int, Worker] = {}
        for worker in self._workers:
            self._tick_worker_satiety(worker, now_ms)
            if worker.dining_canteen is not None and self._registry is not None and world is not None:
                from game.buildings.canteen import Canteen
                from game.worker_dining import update_dining_runtime

                canteen = worker.dining_canteen
                if isinstance(canteen, Canteen) and canteen in self._registry.all():
                    update_dining_runtime(
                        worker,
                        canteen=canteen,
                        world=world,
                        worker_manager=self,
                        registry=self._registry,
                        now_ms=now_ms,
                    )
                    continue
            worker.update(now_ms)
            updater = self._updaters.get(worker.type_tag)
            if updater is not None:
                updater(worker, now_ms, world)
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
        if building.type_tag == "FIELD":
            worker.target_tile = worker.current_tile
            worker.path = []
            worker.segment_progress = 0.0
            return
        approach_tiles = self._approach_tiles(building)
        target = approach_tiles[0] if approach_tiles else None
        if building.grid_pos is not None:
            gx, gy = building.grid_pos
            w, h = type(building).footprint
            preferred_x = gx + w // 2
            bottom_tiles = [tile for tile in approach_tiles if tile[1] == gy + h]
            if bottom_tiles:
                target = min(bottom_tiles, key=lambda tile: (abs(tile[0] - preferred_x), tile[0]))
        if target is not None:
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
        source = self._building_bonus_source(building)
        for stat, delta in building_worker_effects(building.type_tag, building.level).items():
            worker.characteristics.add_permanent(source, stat, delta)


