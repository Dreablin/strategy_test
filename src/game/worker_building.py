"""Builder runtime helpers for WorkerManager."""

from __future__ import annotations

from typing import Any

from game.pathfinding import find_path_to_any_bfs
from game.worker_geometry import building_center_tile
from game.worker_hunger import try_builder_hunger_after_completion_or_idle
from game.worker_models import Worker


class WorkerBuildingMixin:
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
                try_builder_hunger_after_completion_or_idle(
                    worker,
                    world=world,
                    registry=self._registry,
                    worker_manager=self,
                    now_ms=int(now_ms),
                )
                return
            if site.builder is worker:
                if worker.state == "moving":
                    worker.idle = False
                    return
                if not site.is_fully_supplied():
                    site.builder = None
                    worker.assigned_building = None
                    worker.idle = True
                    worker.state = "idle"
                    return
                if site.build_started_ms is None:
                    worker.state = "entering_site"
                    self._park_worker_inside_building(worker, building)
                    site.build_started_ms = int(now_ms)
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
            best_path = find_path_to_any_bfs(
                world,
                worker.current_tile,
                self._builder_destination_tiles(target),
                blocked,
            )
            if best_path is None:
                continue
            worker.assigned_building = target
            target.construction_site.builder = worker
            worker.start_move(best_path, started_ms=now_ms)
            return
        try_builder_hunger_after_completion_or_idle(
            worker,
            world=world,
            registry=self._registry,
            worker_manager=self,
            now_ms=int(now_ms),
        )
        return True
