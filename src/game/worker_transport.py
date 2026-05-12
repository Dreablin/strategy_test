"""Carrier transport queue helpers for WorkerManager."""

from __future__ import annotations

from typing import Any

from game.buildings.base import Building
from game.buildings.town_hall import TownHall
from game.pathfinding import find_path_bfs
from game.transport_tasks import (
    _processor_accepts_resource,
    _water_amount,
    _water_capacity,
    bakery_input_transport_tasks,
    bakery_output_transport_tasks,
    canteen_input_transport_tasks,
    chicken_farm_output_transport_tasks,
    cow_farm_beef_output_transport_tasks,
    cow_farm_hide_output_transport_tasks,
    construction_transport_tasks,
    farm_wheat_output_transport_tasks,
    iron_mine_output_transport_tasks,
    vineyard_farm_grape_output_transport_tasks,
    mill_input_transport_tasks,
    mill_output_transport_tasks,
    sawmill_input_transport_tasks,
    sawmill_output_transport_tasks,
    water_input_transport_tasks,
    restaurant_input_transport_tasks,
    winery_input_transport_tasks,
    winery_output_transport_tasks,
)
from game.worker_constants import CARRIER_INTERACT_MS
from game.worker_geometry import building_center_tile
from game.worker_hunger import try_carrier_hunger_after_delivery_or_idle
from game.worker_models import TransportTask, Worker


class WorkerTransportMixin:
    def _primary_town_hall(self) -> TownHall | None:
        if self._registry is None:
            return None
        for building in self._registry.all():
            if isinstance(building, TownHall):
                return building
        return None

    def _inbound_resource_count(
        self,
        target: Building,
        resource: str,
        planned_counts: dict[tuple[int, str], int] | None = None,
    ) -> int:
        key = str(resource)
        total = 0
        for task in self._transport_queue:
            if task.target is target and task.resource == key:
                total += 1
        for worker in self._workers:
            task = worker.transport_task
            if task is not None and task.target is target and task.resource == key:
                total += 1
        if planned_counts is not None:
            total += int(planned_counts.get((id(target), key), 0))
        return total

    def _processor_input_space_after_inbound(
        self,
        building: Building,
        resource: str,
        planned_counts: dict[tuple[int, str], int] | None = None,
    ) -> int:
        input_capacity = getattr(building, "input_capacity", None)
        input_amount = getattr(building, "input_amount", None)
        if not callable(input_capacity) or not callable(input_amount):
            return 0
        capacity = int(input_capacity())
        actual = int(input_amount())
        inbound = self._inbound_resource_count(building, resource, planned_counts)
        return max(0, capacity - actual - inbound)

    def _building_accepts_processor_input(self, building: Building, resource: str) -> bool:
        return _processor_accepts_resource(building, resource)

    def _processor_input_target_for_resource(
        self,
        resource: str,
        *,
        source: Building | None = None,
        planned_counts: dict[tuple[int, str], int] | None = None,
    ) -> Building | None:
        if self._registry is None:
            return None
        resource_key = str(resource)
        source_center: tuple[int, int] | None = None
        if source is not None and source.grid_pos is not None:
            source_center = building_center_tile(source)

        candidates: list[tuple[int, int, int, Building]] = []
        for idx, building in enumerate(self._registry.all()):
            if not self._building_accepts_processor_input(building, resource_key):
                continue
            if getattr(building, "is_under_construction", False):
                continue
            if not getattr(building, "active", False):
                continue
            space = self._processor_input_space_after_inbound(building, resource_key, planned_counts)
            if space <= 0:
                continue
            distance = 0
            if source_center is not None and building.grid_pos is not None:
                target_center = building_center_tile(building)
                distance = abs(target_center[0] - source_center[0]) + abs(target_center[1] - source_center[1])
            candidates.append((distance, -space, idx, building))
        if not candidates:
            return None
        candidates.sort(key=lambda item: (item[0], item[1], item[2]))
        return candidates[0][3]

    def _construction_target_for_resource(self, resource: str) -> Building | None:
        if self._registry is None:
            return None
        key = str(resource).lower()
        inbound_counts = self._construction_inbound_counts()
        for building in self._registry.all():
            if not building.is_under_construction:
                continue
            site = building.construction_site
            if site is None:
                continue
            remaining = int(site.remaining_resources().get(key, 0))
            inbound = int(inbound_counts.get((id(building), key), 0))
            if remaining - inbound > 0:
                return building
        return None

    def _construction_inbound_counts(self) -> dict[tuple[int, str], int]:
        counts: dict[tuple[int, str], int] = {}
        for task in self._transport_queue:
            if task.returning_to_town_hall or task.purpose != "construction":
                continue
            key = (id(task.target), str(task.resource).lower())
            counts[key] = counts.get(key, 0) + 1
        for worker in self._workers:
            task = worker.transport_task
            if task is None or task.returning_to_town_hall or task.purpose != "construction":
                continue
            key = (id(task.target), str(task.resource).lower())
            counts[key] = counts.get(key, 0) + 1
        return counts

    def _pending_well_water_pickup_counts(self) -> dict[int, int]:
        """Water units still at wells: queued tasks + carriers not yet loaded."""
        counts: dict[int, int] = {}
        for task in self._transport_queue:  # type: ignore[attr-defined]
            if task.resource != "water" or task.source.type_tag != "WELL":
                continue
            wid = id(task.source)
            counts[wid] = counts.get(wid, 0) + 1
        for worker in self._workers:  # type: ignore[attr-defined]
            t = worker.transport_task
            if t is None or t.resource != "water" or t.source.type_tag != "WELL":
                continue
            if worker.carrying is not None:
                continue
            wid = id(t.source)
            counts[wid] = counts.get(wid, 0) + 1
        return counts

    def _water_inbound_counts_by_target_id(self) -> dict[int, int]:
        """Water deliveries already targeting each building (queue + in-flight)."""
        counts: dict[int, int] = {}
        for task in self._transport_queue:  # type: ignore[attr-defined]
            if task.resource != "water":
                continue
            tid = id(task.target)
            counts[tid] = counts.get(tid, 0) + 1
        for worker in self._workers:  # type: ignore[attr-defined]
            t = worker.transport_task
            if t is None or t.resource != "water":
                continue
            tid = id(t.target)
            counts[tid] = counts.get(tid, 0) + 1
        return counts

    def _next_transport_task(self) -> TransportTask | None:
        if self._registry is None:
            return None
        known = set(self._registry.all())
        eligible: list[tuple[int, TransportTask]] = []
        stale_indices: list[int] = []
        for idx, task in enumerate(self._transport_queue):
            if task.source not in known or task.target not in known:
                stale_indices.append(idx)
                continue
            if (
                not task.returning_to_town_hall
                and task.purpose != "construction"
                and bool(getattr(task.target, "is_under_construction", False))
            ):
                stale_indices.append(idx)
                continue
            site = getattr(task.target, "construction_site", None)
            if task.purpose == "construction":
                if not bool(getattr(task.target, "is_under_construction", False)) or site is None:
                    stale_indices.append(idx)
                    continue
                remaining = int(site.remaining_resources().get(str(task.resource).lower(), 0))
                if remaining <= 0:
                    stale_indices.append(idx)
                    continue
            has_storage_source = False
            if hasattr(task.source, "stored") and int(getattr(task.source, "stored", 0)) > 0:
                has_storage_source = True
            elif task.resource == "grapes" and getattr(task.source, "type_tag", "") == "VINEYARD_FARM":
                grapes_amount = getattr(task.source, "grapes_amount", None)
                if callable(grapes_amount) and int(grapes_amount()) > 0:
                    has_storage_source = True
            elif task.resource == "wood" and hasattr(task.source, "input_amount"):
                has_storage_source = int(task.source.input_amount()) > 0  # type: ignore[attr-defined]
            elif task.resource == "boards" and hasattr(task.source, "output_amount"):
                has_storage_source = int(task.source.output_amount()) > 0  # type: ignore[attr-defined]
            elif task.resource == "flour" and hasattr(task.source, "output_amount"):
                has_storage_source = int(task.source.output_amount()) > 0  # type: ignore[attr-defined]
            elif task.resource == "bread" and hasattr(task.source, "output_amount"):
                has_storage_source = int(task.source.output_amount()) > 0  # type: ignore[attr-defined]
            elif task.resource == "chicken" and hasattr(task.source, "output_amount"):
                has_storage_source = int(task.source.output_amount()) > 0  # type: ignore[attr-defined]
            elif task.resource == "beef" and hasattr(task.source, "beef_amount"):
                has_storage_source = int(task.source.beef_amount()) > 0  # type: ignore[attr-defined]
            elif task.resource == "hide" and hasattr(task.source, "hide_amount"):
                has_storage_source = int(task.source.hide_amount()) > 0  # type: ignore[attr-defined]
            elif task.resource == "wine" and hasattr(task.source, "output_amount"):
                has_storage_source = int(task.source.output_amount()) > 0  # type: ignore[attr-defined]
            elif task.resource == "water" and task.source.type_tag == "WELL":
                has_storage_source = _water_amount(task.source) > 0
            if task.resource == "beef" and getattr(task.source, "type_tag", "") == "COW_FARM":
                if int(task.source.beef_amount()) <= 0:  # type: ignore[attr-defined]
                    stale_indices.append(idx)
                    continue
            if task.resource == "hide" and getattr(task.source, "type_tag", "") == "COW_FARM":
                if int(task.source.hide_amount()) <= 0:  # type: ignore[attr-defined]
                    stale_indices.append(idx)
                    continue
            has_warehouse_source = hasattr(task.source, "warehouse_amount") and int(
                task.source.warehouse_amount(task.resource)  # type: ignore[attr-defined]
            ) > 0
            if task.resource == "water":
                water_capacity = _water_capacity(task.target)
                water_amount = _water_amount(task.target)
                if water_amount >= water_capacity:
                    stale_indices.append(idx)
                    continue
            if not has_storage_source and not has_warehouse_source:
                if task.resource == "wheat" and task.source.type_tag == "FARM":
                    stale_indices.append(idx)
                elif task.resource == "grapes" and getattr(task.source, "type_tag", "") == "VINEYARD_FARM":
                    stale_indices.append(idx)
                continue
            eligible.append((idx, task))
        for idx in reversed(stale_indices):
            self._transport_queue.pop(idx)
        if not eligible:
            return None
        eligible_sorted = sorted(eligible, key=lambda item: (-int(item[1].priority), item[0]))
        for _idx, best_task in eligible_sorted:
            if best_task not in self._transport_queue:
                continue
            self._transport_queue.remove(best_task)
            return best_task
        return None

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

    def _clear_carrier_transport(self, worker: Worker, *, exit_building: Building | None = None) -> None:
        worker.transport_task = None
        worker.carrying = None
        worker.path = []
        worker.target_tile = None
        worker.segment_progress = 0.0
        worker.segment_started_ms = 0
        worker.camp_wait_until_ms = 0
        worker.state = "idle"
        worker.idle = True
        worker.stand_tile = worker.current_tile
        if exit_building is not None:
            self._move_worker_to_building_approach(worker, exit_building)  # type: ignore[attr-defined]

    def _requeue_failed_pickup(self, worker: Worker, task: TransportTask) -> None:
        self._transport_queue.append(task)
        known = set(self._registry.all()) if self._registry is not None else set()
        exit_building = task.source if task.source in known else None
        self._clear_carrier_transport(worker, exit_building=exit_building)

    def _drop_failed_pickup(self, worker: Worker, task: TransportTask) -> None:
        known = set(self._registry.all()) if self._registry is not None else set()
        exit_building = task.source if task.source in known else None
        self._clear_carrier_transport(worker, exit_building=exit_building)

    def _transport_task_invalid(self, task: TransportTask) -> bool:
        if self._registry is None:
            return True
        known = set(self._registry.all())
        if task.returning_to_town_hall:
            return task.target not in known
        if task.source not in known or task.target not in known:
            return True
        if task.purpose == "construction":
            if not bool(getattr(task.target, "is_under_construction", False)):
                return True
            site = getattr(task.target, "construction_site", None)
            if site is None:
                return True
            return int(site.remaining_resources().get(str(task.resource).lower(), 0)) <= 0
        if not task.returning_to_town_hall and (
            bool(getattr(task.target, "is_under_construction", False))
        ):
            return True
        return False

    def _reroute_or_cancel_invalid_transport(self, worker: Worker, task: TransportTask, now_ms: int) -> bool:
        if not self._transport_task_invalid(task):
            return True
        if worker.carrying is None:
            known = set(self._registry.all()) if self._registry is not None else set()
            exit_building = task.source if task.source in known else None
            self._clear_carrier_transport(worker, exit_building=exit_building)
            return False
        if worker.carrying == "water":
            self._clear_carrier_transport(worker)
            return False

        town_hall = self._primary_town_hall()
        if town_hall is None:
            self._clear_carrier_transport(worker)
            return False

        task.source = town_hall
        task.target = town_hall
        task.priority = 10
        task.returning_to_town_hall = True
        task.purpose = "return"
        worker.transport_task = task
        if not self._start_move_to_building(worker, town_hall, now_ms):
            town_hall.add_to_warehouse(worker.carrying, 1)
            self._clear_carrier_transport(worker)
            return False
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
                try_carrier_hunger_after_delivery_or_idle(
                    worker,
                    world=world,
                    registry=self._registry,
                    worker_manager=self,
                    now_ms=int(now_ms),
                )
                return
            worker.transport_task = task
            worker.carrying = None
            if not self._start_move_to_building(worker, task.source, now_ms):
                self._transport_queue.insert(0, task)
                worker.transport_task = None
                worker.state = "idle"
                worker.idle = True
            return

        if not self._reroute_or_cancel_invalid_transport(worker, task, now_ms):
            return
        task = worker.transport_task
        if task is None:
            return

        if worker.state in {"moving", "returning"}:
            return

        if worker.carrying is None:
            if worker.state != "carrier_loading":
                self._park_worker_inside_building(worker, task.source)
                worker.state = "carrier_loading"
                wait_ms = CARRIER_INTERACT_MS
                worker.camp_wait_until_ms = now_ms + wait_ms
                return
            if now_ms < worker.camp_wait_until_ms:
                return
            if task.source not in self._registry.all() or task.target not in self._registry.all():
                worker.transport_task = None
                worker.state = "idle"
                worker.idle = True
                return
            if not hasattr(task.source, "take_from_storage"):
                if task.resource == "grapes" and getattr(task.source, "type_tag", "") == "VINEYARD_FARM":
                    try:
                        task.source.take_grapes_from_storage(1)  # type: ignore[attr-defined]
                    except ValueError:
                        self._drop_failed_pickup(worker, task)
                        return
                elif task.resource == "wood" and hasattr(task.source, "take_wood_in"):
                    try:
                        task.source.take_wood_in(1)  # type: ignore[attr-defined]
                    except ValueError:
                        self._drop_failed_pickup(worker, task)
                        return
                elif task.resource == "boards" and hasattr(task.source, "take_boards_out"):
                    try:
                        task.source.take_boards_out(1)  # type: ignore[attr-defined]
                    except ValueError:
                        self._drop_failed_pickup(worker, task)
                        return
                elif task.resource == "flour" and hasattr(task.source, "take_flour_out"):
                    try:
                        task.source.take_flour_out(1)  # type: ignore[attr-defined]
                    except ValueError:
                        self._drop_failed_pickup(worker, task)
                        return
                elif task.resource == "bread" and hasattr(task.source, "take_bread_out"):
                    try:
                        task.source.take_bread_out(1)  # type: ignore[attr-defined]
                    except ValueError:
                        self._drop_failed_pickup(worker, task)
                        return
                elif task.resource == "chicken" and hasattr(task.source, "take_chicken_out"):
                    try:
                        task.source.take_chicken_out(1)  # type: ignore[attr-defined]
                    except ValueError:
                        self._drop_failed_pickup(worker, task)
                        return
                elif task.resource == "beef" and hasattr(task.source, "take_beef_out"):
                    try:
                        task.source.take_beef_out(1)  # type: ignore[attr-defined]
                    except ValueError:
                        self._drop_failed_pickup(worker, task)
                        return
                elif task.resource == "hide" and hasattr(task.source, "take_hide_out"):
                    try:
                        task.source.take_hide_out(1)  # type: ignore[attr-defined]
                    except ValueError:
                        self._drop_failed_pickup(worker, task)
                        return
                elif task.resource == "wine" and hasattr(task.source, "take_wine"):
                    try:
                        task.source.take_wine(1)  # type: ignore[attr-defined]
                    except ValueError:
                        self._drop_failed_pickup(worker, task)
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
                        self._requeue_failed_pickup(worker, task)
                        return
            else:
                try:
                    task.source.take_from_storage(1)  # type: ignore[attr-defined]
                except ValueError:
                    self._drop_failed_pickup(worker, task)
                    return
            worker.carrying = task.resource
            if isinstance(task.source, TownHall):
                # Town Hall center can trap pathfinding because it is fully enclosed by occupied tiles.
                self._move_worker_to_building_approach(worker, task.source)
            if not self._start_move_to_building(worker, task.target, now_ms):
                if task.resource == "water" and task.source.type_tag == "WELL" and hasattr(
                    task.source, "add_to_storage"
                ):
                    task.source.add_to_storage(1)  # type: ignore[attr-defined]
                elif task.resource == "wood" and hasattr(task.source, "add_wood_in"):
                    task.source.add_wood_in(1)  # type: ignore[attr-defined]
                elif task.resource == "boards" and hasattr(task.source, "add_boards_out"):
                    task.source.add_boards_out(1)  # type: ignore[attr-defined]
                elif task.resource == "flour" and hasattr(task.source, "add_flour_out"):
                    task.source.add_flour_out(1)  # type: ignore[attr-defined]
                elif task.resource == "bread" and hasattr(task.source, "add_bread_out"):
                    task.source.add_bread_out(1)  # type: ignore[attr-defined]
                elif task.resource == "chicken" and hasattr(task.source, "add_chicken_out"):
                    task.source.add_chicken_out(1)  # type: ignore[attr-defined]
                elif task.resource == "beef" and hasattr(task.source, "add_beef_out"):
                    task.source.add_beef_out(1)  # type: ignore[attr-defined]
                elif task.resource == "hide" and hasattr(task.source, "add_hide_out"):
                    task.source.add_hide_out(1)  # type: ignore[attr-defined]
                elif task.resource == "grapes" and getattr(task.source, "type_tag", "") == "VINEYARD_FARM":
                    task.source.add_grapes_to_storage(1)  # type: ignore[attr-defined]
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
        if task.returning_to_town_hall:
            if hasattr(task.target, "add_to_warehouse"):
                task.target.add_to_warehouse(task.resource, 1)  # type: ignore[attr-defined]
        elif site is not None:
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
        elif task.purpose == "construction":
            town_hall = self._primary_town_hall()
            if town_hall is not None:
                town_hall.add_to_warehouse(task.resource, 1)
                delivered_target = town_hall
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
        elif task.resource == "wheat" and hasattr(task.target, "add_wheat_in"):
            if int(task.target.input_amount()) < int(task.target.input_capacity()):  # type: ignore[attr-defined]
                task.target.add_wheat_in(1)  # type: ignore[attr-defined]
            else:
                town_hall = self._primary_town_hall()
                if town_hall is not None:
                    town_hall.add_to_warehouse(task.resource, 1)
                    delivered_target = town_hall
                elif hasattr(task.target, "add_to_warehouse"):
                    task.target.add_to_warehouse(task.resource, 1)  # type: ignore[attr-defined]
        elif task.resource == "flour" and hasattr(task.target, "add_flour_in"):
            if int(task.target.input_amount()) < int(task.target.input_capacity()):  # type: ignore[attr-defined]
                task.target.add_flour_in(1)  # type: ignore[attr-defined]
            else:
                town_hall = self._primary_town_hall()
                if town_hall is not None:
                    town_hall.add_to_warehouse(task.resource, 1)
                    delivered_target = town_hall
                elif hasattr(task.target, "add_to_warehouse"):
                    task.target.add_to_warehouse(task.resource, 1)  # type: ignore[attr-defined]
        elif task.resource == "grapes" and hasattr(task.target, "add_grapes"):
            if int(task.target.input_amount()) < int(task.target.input_capacity()):  # type: ignore[attr-defined]
                task.target.add_grapes(1)  # type: ignore[attr-defined]
            else:
                town_hall = self._primary_town_hall()
                if town_hall is not None:
                    town_hall.add_to_warehouse(task.resource, 1)
                    delivered_target = town_hall
                elif hasattr(task.target, "add_to_warehouse"):
                    task.target.add_to_warehouse(task.resource, 1)  # type: ignore[attr-defined]
        elif task.target.type_tag == "CANTEEN" and task.resource in ("chicken", "bread"):
            canteen = task.target
            cap = int(canteen.local_storage_capacity(task.resource))
            amt = int(canteen.local_storage_amount(task.resource))
            if amt < cap:
                canteen.add_local_storage(task.resource, 1)
            else:
                town_hall = self._primary_town_hall()
                if town_hall is not None:
                    town_hall.add_to_warehouse(task.resource, 1)
                    delivered_target = town_hall
        elif task.target.type_tag == "RESTAURANT" and hasattr(task.target, "add_local_storage"):
            cap = int(task.target.local_storage_capacity(task.resource))
            amt = int(task.target.local_storage_amount(task.resource))
            if amt < cap:
                task.target.add_local_storage(task.resource, 1)
            else:
                town_hall = self._primary_town_hall()
                if town_hall is not None:
                    town_hall.add_to_warehouse(task.resource, 1)
                    delivered_target = town_hall
        elif task.resource == "water" and hasattr(task.target, "add_water_in"):
            if _water_amount(task.target) < _water_capacity(task.target):
                task.target.add_water_in(1)  # type: ignore[attr-defined]
        elif task.resource == "boards" and hasattr(task.target, "add_to_warehouse"):
            task.target.add_to_warehouse(task.resource, 1)  # type: ignore[attr-defined]
        elif hasattr(task.target, "add_to_warehouse"):
            task.target.add_to_warehouse(task.resource, 1)  # type: ignore[attr-defined]
        self._move_worker_to_building_approach(worker, delivered_target)
        worker.carrying = None
        worker.transport_task = None
        worker.state = "idle"
        worker.idle = True
        try_carrier_hunger_after_delivery_or_idle(
            worker,
            world=world,
            registry=self._registry,
            worker_manager=self,
            now_ms=int(now_ms),
        )

    def _enqueue_desired_transport_tasks(
        self,
        desired: list[TransportTask],
        *,
        count_carried_town_hall_delivery: bool = True,
        dedup_skip_carrying_workers: bool = False,
    ) -> None:
        desired_counts: dict[tuple[int, int, str, int, str], int] = {}
        for task in desired:
            key = (id(task.source), id(task.target), task.resource, int(task.priority), task.purpose)
            desired_counts[key] = desired_counts.get(key, 0) + 1

        existing_counts: dict[tuple[int, int, str, int, str], int] = {}
        for task in self._transport_queue:  # type: ignore[attr-defined]
            key = (id(task.source), id(task.target), task.resource, int(task.priority), task.purpose)
            existing_counts[key] = existing_counts.get(key, 0) + 1
        for worker in self._workers:  # type: ignore[attr-defined]
            task = worker.transport_task
            if task is None:
                continue
            if dedup_skip_carrying_workers and worker.carrying is not None:
                continue
            if (
                not count_carried_town_hall_delivery
                and task.source.type_tag == "TOWN_HALL"
                and worker.carrying is not None
            ):
                continue
            key = (id(task.source), id(task.target), task.resource, int(task.priority), task.purpose)
            existing_counts[key] = existing_counts.get(key, 0) + 1

        for task in desired:
            key = (id(task.source), id(task.target), task.resource, int(task.priority), task.purpose)
            if existing_counts.get(key, 0) >= desired_counts.get(key, 0):
                continue
            self.enqueue_transport_task(  # type: ignore[attr-defined]
                resource=task.resource,
                source=task.source,
                target=task.target,
                amount=1,
                priority=task.priority,
                purpose=task.purpose,
            )
            existing_counts[key] = existing_counts.get(key, 0) + 1

    def _enqueue_construction_transport_tasks(self) -> None:
        if self._registry is None:  # type: ignore[attr-defined]
            return
        for task in construction_transport_tasks(
            self._registry,
            inbound_counts=self._construction_inbound_counts(),
        ):
            self.enqueue_transport_task(  # type: ignore[attr-defined]
                resource=task.resource,
                source=task.source,
                target=task.target,
                amount=1,
                priority=task.priority,
                purpose=task.purpose,
            )

    def _enqueue_sawmill_refill_tasks(self) -> None:
        if self._registry is None:  # type: ignore[attr-defined]
            return
        self._enqueue_desired_transport_tasks(sawmill_input_transport_tasks(self._registry))  # type: ignore[attr-defined]

    def _enqueue_sawmill_output_tasks(self) -> None:
        if self._registry is None:  # type: ignore[attr-defined]
            return
        self._enqueue_desired_transport_tasks(sawmill_output_transport_tasks(self._registry))  # type: ignore[attr-defined]

    def _enqueue_mill_refill_tasks(self) -> None:
        if self._registry is None:  # type: ignore[attr-defined]
            return
        self._enqueue_desired_transport_tasks(mill_input_transport_tasks(self._registry))  # type: ignore[attr-defined]

    def _enqueue_mill_output_tasks(self) -> None:
        if self._registry is None:  # type: ignore[attr-defined]
            return
        desired: list[TransportTask] = []
        planned_counts: dict[tuple[int, str], int] = {}
        town_hall = self._primary_town_hall()  # type: ignore[attr-defined]
        for task in mill_output_transport_tasks(self._registry):  # type: ignore[attr-defined]
            target = self._processor_input_target_for_resource(  # type: ignore[attr-defined]
                task.resource,
                source=task.source,
                planned_counts=planned_counts,
            )
            if target is None:
                target = town_hall
            if target is None:
                continue
            desired.append(
                TransportTask(
                    resource=task.resource,
                    source=task.source,
                    target=target,
                    priority=task.priority,
                )
            )
            if self._building_accepts_processor_input(target, task.resource):  # type: ignore[attr-defined]
                key = (id(target), task.resource)
                planned_counts[key] = planned_counts.get(key, 0) + 1
        self._enqueue_desired_transport_tasks(desired)

    def _enqueue_bakery_refill_tasks(self) -> None:
        if self._registry is None:  # type: ignore[attr-defined]
            return
        self._enqueue_desired_transport_tasks(bakery_input_transport_tasks(self._registry))  # type: ignore[attr-defined]

    def _enqueue_winery_input_tasks(self) -> None:
        if self._registry is None:  # type: ignore[attr-defined]
            return
        self._enqueue_desired_transport_tasks(winery_input_transport_tasks(self._registry))  # type: ignore[attr-defined]

    def _enqueue_winery_output_tasks(self) -> None:
        if self._registry is None:  # type: ignore[attr-defined]
            return
        self._enqueue_desired_transport_tasks(winery_output_transport_tasks(self._registry))  # type: ignore[attr-defined]

    def _enqueue_canteen_input_tasks(self) -> None:
        if self._registry is None:  # type: ignore[attr-defined]
            return
        desired: list[TransportTask] = []
        planned_counts: dict[tuple[int, str], int] = {}
        for task in canteen_input_transport_tasks(self._registry):
            if task.resource not in {"chicken", "bread"}:
                continue
            target = task.target
            cap = int(target.local_storage_capacity(task.resource))
            amt = int(target.local_storage_amount(task.resource))
            inbound = self._inbound_resource_count(target, task.resource, planned_counts)  # type: ignore[attr-defined]
            if amt + inbound >= cap:
                continue
            desired.append(task)
            key = (id(target), task.resource)
            planned_counts[key] = planned_counts.get(key, 0) + 1
        self._enqueue_desired_transport_tasks(
            desired,
            count_carried_town_hall_delivery=False,
        )

    def _enqueue_restaurant_input_tasks(self, resource: str) -> None:
        if self._registry is None:  # type: ignore[attr-defined]
            return
        desired: list[TransportTask] = []
        planned_counts: dict[tuple[int, str], int] = {}
        for task in restaurant_input_transport_tasks(self._registry, resource):
            target = task.target
            cap = int(target.local_storage_capacity(task.resource))
            amt = int(target.local_storage_amount(task.resource))
            inbound = self._inbound_resource_count(target, task.resource, planned_counts)  # type: ignore[attr-defined]
            if amt + inbound >= cap:
                continue
            desired.append(task)
            key = (id(target), task.resource)
            planned_counts[key] = planned_counts.get(key, 0) + 1
        self._enqueue_desired_transport_tasks(
            desired,
            count_carried_town_hall_delivery=False,
        )

    def _enqueue_water_input_tasks(self) -> None:
        if self._registry is None:  # type: ignore[attr-defined]
            return
        desired = water_input_transport_tasks(
            self._registry,
            pending_pickups_by_well_id=self._pending_well_water_pickup_counts(),
            inbound_water_by_target_id=self._water_inbound_counts_by_target_id(),
        )
        self._enqueue_desired_transport_tasks(desired, dedup_skip_carrying_workers=True)

    def _enqueue_bakery_output_tasks(self) -> None:
        if self._registry is None:  # type: ignore[attr-defined]
            return
        self._enqueue_desired_transport_tasks(bakery_output_transport_tasks(self._registry))  # type: ignore[attr-defined]

    def _enqueue_chicken_farm_output_tasks(self) -> None:
        if self._registry is None:  # type: ignore[attr-defined]
            return
        self._enqueue_desired_transport_tasks(chicken_farm_output_transport_tasks(self._registry))  # type: ignore[attr-defined]

    def _enqueue_cow_farm_beef_output_tasks(self) -> None:
        if self._registry is None:  # type: ignore[attr-defined]
            return
        self._enqueue_desired_transport_tasks(cow_farm_beef_output_transport_tasks(self._registry))  # type: ignore[attr-defined]

    def _enqueue_cow_farm_hide_output_tasks(self) -> None:
        if self._registry is None:  # type: ignore[attr-defined]
            return
        self._enqueue_desired_transport_tasks(cow_farm_hide_output_transport_tasks(self._registry))  # type: ignore[attr-defined]

    def _enqueue_iron_mine_output_tasks(self) -> None:
        if self._registry is None:  # type: ignore[attr-defined]
            return
        self._enqueue_desired_transport_tasks(iron_mine_output_transport_tasks(self._registry))  # type: ignore[attr-defined]

    def _enqueue_farm_wheat_output_tasks(self) -> None:
        if self._registry is None:  # type: ignore[attr-defined]
            return
        desired: list[TransportTask] = []
        planned_counts: dict[tuple[int, str], int] = {}
        town_hall = self._primary_town_hall()  # type: ignore[attr-defined]
        for task in farm_wheat_output_transport_tasks(self._registry):  # type: ignore[attr-defined]
            target = self._processor_input_target_for_resource(  # type: ignore[attr-defined]
                task.resource,
                source=task.source,
                planned_counts=planned_counts,
            )
            if target is None:
                target = town_hall
            if target is None:
                continue
            desired.append(
                TransportTask(
                    resource=task.resource,
                    source=task.source,
                    target=target,
                    priority=task.priority,
                )
            )
            if self._building_accepts_processor_input(target, task.resource):  # type: ignore[attr-defined]
                key = (id(target), task.resource)
                planned_counts[key] = planned_counts.get(key, 0) + 1
        self._enqueue_desired_transport_tasks(desired)

    def _enqueue_vineyard_farm_grape_output_tasks(self) -> None:
        if self._registry is None:  # type: ignore[attr-defined]
            return
        self._enqueue_desired_transport_tasks(
            vineyard_farm_grape_output_transport_tasks(self._registry),
        )
