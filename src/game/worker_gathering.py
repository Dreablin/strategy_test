"""Gatherer, forester, and miner runtime helpers for WorkerManager."""

from __future__ import annotations

import random
from typing import Any

from game.buildings.base import Building
from game.pathfinding import find_path_bfs
from game.worker_constants import (
    CHOP_DURATION_MS,
    FORESTER_PLANT_RADIUS,
    FORESTER_REST_MS,
    FORESTER_RETURN_RETRY_MS,
    FORESTER_TARGET_RANDOM_TRIES,
    FORESTER_TARGET_RETRY_MS,
    LUMBER_CAMP_RESOURCE_RADIUS,
    LUMBERJACK_REST_MS,
    MINE_DURATION_MS,
    PLANT_DURATION_MS,
    STONE_MINE_RESOURCE_RADIUS,
    STONECUTTER_REST_MS,
)
from game.worker_geometry import building_center_tile
from game.worker_hunger import try_hunger_canteen_after_completed_cycle
from game.worker_models import Worker
from game.world import find_nearest_free_stone, find_nearest_free_tree


class WorkerGatheringMixin:
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
                self._try_blocked_cycle_hunger(worker, now_ms)
                return
            if hasattr(camp, "is_storage_full") and camp.is_storage_full():
                # Keep waiting inside the camp while storage is full.
                worker.camp_wait_until_ms = now_ms + 1_000
                self._try_blocked_cycle_hunger(worker, now_ms)
                return
            depart_ms = worker.camp_wait_until_ms
            if not self._start_gather_cycle(worker, camp, depart_ms, world_query=gather_state["world_query"]):
                # No target/path right now: stay inside camp and retry later.
                self._park_worker_inside_camp(worker, camp)
                worker.camp_wait_until_ms = now_ms + 1_000
                self._try_blocked_cycle_hunger(worker, now_ms)
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
                    target = self._processor_input_target_for_resource(resource, source=camp)
                    priority = 0
                if target is None:
                    target = self._primary_town_hall()
                if target is not None:
                    self.enqueue_transport_task(
                        resource=resource,
                        source=camp,
                        target=target,
                        amount=1,
                        priority=priority,
                        purpose="construction" if getattr(target, "is_under_construction", False) else "generic",
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
            if self._registry is not None:
                w = getattr(self._registry, "_world", None)
                if w is not None:
                    try_hunger_canteen_after_completed_cycle(
                        worker,
                        world=w,
                        registry=self._registry,
                        worker_manager=self,
                        now_ms=int(now_ms),
                    )
            return

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
                self._try_blocked_cycle_hunger(worker, now_ms)
                return
            if worker.camp_wait_until_ms <= 0:
                worker.camp_wait_until_ms = now_ms + FORESTER_REST_MS
            if now_ms < worker.camp_wait_until_ms:
                return
            # Start walking from "now" to preserve smooth interpolation.
            depart_ms = now_ms
            if not self._start_forester_cycle(worker, hut, depart_ms, world):
                worker.camp_wait_until_ms = now_ms + FORESTER_TARGET_RETRY_MS
                self._try_blocked_cycle_hunger(worker, now_ms)
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
                self._try_blocked_cycle_hunger(worker, now_ms)
            return

        if worker.state == "return_path_blocked":
            if now_ms < worker.camp_wait_until_ms:
                return
            if self._start_return_to_camp(worker, now_ms):
                worker.camp_wait_until_ms = 0
                return
            worker.camp_wait_until_ms = now_ms + FORESTER_RETURN_RETRY_MS
            self._try_blocked_cycle_hunger(worker, now_ms)
            return

        if worker.state == "arrived_camp":
            self._park_forester_inside_hut(worker, hut)
            worker.target_tile = None
            worker.chop_started_ms = 0
            worker.chop_duration_ms = CHOP_DURATION_MS
            worker.camp_wait_until_ms = now_ms + FORESTER_REST_MS
            if self._registry is not None and world is not None:
                try_hunger_canteen_after_completed_cycle(
                    worker,
                    world=world,
                    registry=self._registry,
                    worker_manager=self,
                    now_ms=int(now_ms),
                )
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


    def _update_miner(self, worker: Worker, now_ms: int, world: Any) -> None:
        mine = worker.assigned_building
        if mine is None or mine.type_tag != "IRON_MINE":
            return
        if mine.is_under_construction:
            return
        center_tile = building_center_tile(mine)
        if worker.state in {"working", "resting", "mining"} and worker.current_tile != center_tile:
            worker.current_tile = center_tile
            if worker.state == "mining":
                worker.state = "working"
                mine.mining_started_ms = 0
            return
        if worker.state == "resting":
            if now_ms < worker.camp_wait_until_ms:
                return
            worker.state = "working"
            worker.camp_wait_until_ms = 0
            worker.idle = False
        if worker.state == "resting":
            return
        if worker.state == "mining":
            started = int(getattr(mine, "mining_started_ms", 0))
            if started <= 0:
                worker.state = "working"
                return
            duration_ms = max(1, int(mine.cycle_ms()))
            mine.mining_duration_ms = duration_ms
            if now_ms - started < duration_ms:
                return
            if hasattr(mine, "is_storage_full") and not mine.is_storage_full():
                mine.add_to_storage(mine.output_count())
            mine.mining_started_ms = 0
            worker.state = "resting"
            worker.camp_wait_until_ms = int(now_ms) + max(0, int(mine.rest_ms()))
            worker.current_tile = center_tile
            worker.idle = False
            reg = self._registry
            if world is not None and reg is not None:
                try_hunger_canteen_after_completed_cycle(
                    worker,
                    world=world,
                    registry=reg,
                    worker_manager=self,
                    now_ms=int(now_ms),
                )
            return
        if hasattr(mine, "is_storage_full") and mine.is_storage_full():
            worker.state = "working"
            worker.current_tile = center_tile
            worker.idle = False
            self._try_blocked_cycle_hunger(worker, now_ms)
            return
        if worker.state != "working":
            return
        if int(getattr(mine, "mining_started_ms", 0)) <= 0:
            mine.mining_started_ms = int(now_ms)
        mine.mining_duration_ms = max(1, int(mine.cycle_ms()))
        worker.state = "mining"
        worker.current_tile = center_tile
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
            x = random.randint(hx - FORESTER_PLANT_RADIUS, hx + FORESTER_PLANT_RADIUS)
            y = random.randint(hy - FORESTER_PLANT_RADIUS, hy + FORESTER_PLANT_RADIUS)
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
        if world_query == "tree":
            radius = LUMBER_CAMP_RESOURCE_RADIUS
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
            radius = STONE_MINE_RESOURCE_RADIUS
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

