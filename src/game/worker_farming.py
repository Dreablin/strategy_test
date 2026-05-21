"""Farmer and wheat field runtime helpers for WorkerManager."""

from __future__ import annotations

from typing import Any

from game.buildings.base import Building
from game.buildings.field import (
    Field,
    WHEAT_EMPTY,
    WHEAT_PHASE_1,
    WHEAT_PHASE_4,
    is_ready_for_sowing,
    on_field_harvest,
)
from game.buildings.vineyard import Vineyard
from game.pathfinding import find_path_bfs
from game.worker_constants import (
    CHOP_DURATION_MS,
    FARMER_FIELD_RADIUS,
    FARMER_NO_TARGET_WORKING_STATE_MS,
    worker_building_action_ms,
    worker_building_rest_ms,
)
from game.worker_geometry import (
    building_center_tile,
    select_farmer_field_target,
    select_ripe_vineyard_target_tile,
)
from game.worker_hunger import try_hunger_canteen_after_completed_cycle
from game.worker_models import Worker


class WorkerFarmingMixin:
    def _update_farmer(self, worker: Worker, now_ms: int, world: Any) -> None:
        if self._registry is None or world is None:
            return
        farm = worker.assigned_building
        if farm is None:
            self._release_field_reservations_for(worker)
            self._release_vineyard_plot_reservations_for(worker)
            return
        if farm.type_tag == "VINEYARD_FARM":
            self._release_field_reservations_for(worker)
            self._update_vineyard_farm_farmer(worker, farm, now_ms, world)
            return
        if farm.type_tag != "FARM":
            self._release_field_reservations_for(worker)
            self._release_vineyard_plot_reservations_for(worker)
            return
        self._release_vineyard_plot_reservations_for(worker)
        self._update_wheat_farm_farmer(worker, farm, now_ms, world)

    def _update_wheat_farm_farmer(self, worker: Worker, farm: Building, now_ms: int, world: Any) -> None:
        if farm.is_under_construction:
            self._release_field_reservations_for(worker)
            return

        # Enter the farm home base first and begin a rest window.
        if worker.state == "working":
            self._park_worker_inside_building(worker, farm)
            worker.state = "resting"
            if worker.camp_wait_until_ms <= now_ms:
                worker.camp_wait_until_ms = now_ms + worker_building_rest_ms(farm.type_tag)
            return

        if worker.state == "resting":
            self._park_worker_inside_building(worker, farm)
            if now_ms < worker.camp_wait_until_ms:
                return
            target_field = self._select_farmer_target_field(farm)
            if target_field is None:
                worker.state = "working_field" if now_ms >= FARMER_NO_TARGET_WORKING_STATE_MS else "resting"
                worker.camp_wait_until_ms = now_ms + 1_000
                self._try_blocked_cycle_hunger(worker, now_ms)
                return
            if not self._reserve_field(target_field, worker):
                worker.state = "working_field" if now_ms >= FARMER_NO_TARGET_WORKING_STATE_MS else "resting"
                worker.camp_wait_until_ms = now_ms + 1_000
                self._try_blocked_cycle_hunger(worker, now_ms)
                return
            if not self._start_farmer_move_to_field(worker, target_field, now_ms, world):
                self._release_field_reservations_for(worker)
                worker.state = "working_field" if now_ms >= FARMER_NO_TARGET_WORKING_STATE_MS else "resting"
                worker.camp_wait_until_ms = now_ms + 1_000
                self._try_blocked_cycle_hunger(worker, now_ms)
                return
            worker.state = "going_to_field"
            worker.target_tree = target_field.grid_pos
            worker.camp_wait_until_ms = 0
            return

        if worker.state == "working_field":
            self._park_worker_inside_building(worker, farm)
            if now_ms < worker.camp_wait_until_ms:
                return
            worker.state = "resting"
            worker.camp_wait_until_ms = now_ms
            return

        if worker.state == "arrived_field":
            field = self._field_at(tuple(worker.current_tile))
            phase = self._read_field_phase(field) if field is not None else WHEAT_PHASE_1
            worker.state = "sowing" if is_ready_for_sowing(phase) else "harvesting"
            worker.chop_started_ms = now_ms
            worker.chop_duration_ms = worker_building_action_ms(farm.type_tag)
            return

        if worker.state == "sowing":
            if now_ms - worker.chop_started_ms < worker.chop_duration_ms:
                return
            target_tile = worker.target_tree
            if target_tile is not None:
                field = self._field_at(target_tile)
                if field is not None:
                    field.sow(now_ms=now_ms)
                self._release_field_reservations_for(worker)
            if self._start_return_to_camp(worker, now_ms):
                return
            worker.state = "arrived_camp"
            return

        if worker.state == "harvesting":
            if now_ms - worker.chop_started_ms < worker.chop_duration_ms:
                return
            target_tile = worker.target_tree
            if target_tile is not None:
                field = self._field_at(target_tile)
                if field is not None:
                    try:
                        on_field_harvest(field.wheat_phase)
                        field.harvest(now_ms=now_ms)
                        worker.carrying = "wheat"
                    except ValueError:
                        worker.carrying = None
                self._release_field_reservations_for(worker)
            if self._start_return_to_camp(worker, now_ms):
                return
            worker.state = "arrived_camp"
            return

        if worker.state == "arrived_camp":
            self._park_worker_inside_building(worker, farm)
            if worker.carrying == "wheat":
                try:
                    farm.add_to_storage(1)  # type: ignore[attr-defined]
                except ValueError:
                    pass
            worker.carrying = None
            worker.target_tree = None
            worker.chop_started_ms = 0
            worker.chop_duration_ms = CHOP_DURATION_MS
            worker.state = "resting"
            worker.camp_wait_until_ms = now_ms + worker_building_rest_ms(farm.type_tag)
            if self._registry is not None and world is not None:
                try_hunger_canteen_after_completed_cycle(
                    worker,
                    world=world,
                    registry=self._registry,
                    worker_manager=self,
                    now_ms=int(now_ms),
                )

    def _update_vineyard_farm_farmer(self, worker: Worker, farm: Building, now_ms: int, world: Any) -> None:
        """Grape plot dispatch: walk to ripe ``VINEYARD``, harvest, deposit to farm storage."""
        if farm.is_under_construction:
            self._release_vineyard_plot_reservations_for(worker)
            return
        if worker.state == "vineyard_harvest_anim_done":
            self._complete_vineyard_farm_harvest(worker, farm, now_ms, world)
            return
        if worker.state == "vineyard_return_path_blocked":
            if now_ms < worker.camp_wait_until_ms:
                return
            if self._start_return_to_camp(worker, now_ms):
                worker.camp_wait_until_ms = 0
                return
            worker.camp_wait_until_ms = now_ms + 1_000
            self._try_blocked_cycle_hunger(worker, now_ms)
            return
        if worker.state == "working":
            self._park_worker_inside_building(worker, farm)
            worker.state = "resting"
            if worker.camp_wait_until_ms <= now_ms:
                worker.camp_wait_until_ms = now_ms + worker_building_rest_ms(farm.type_tag)
            return
        if worker.state == "resting":
            self._park_worker_inside_building(worker, farm)
            if now_ms < worker.camp_wait_until_ms:
                return
            if hasattr(farm, "grapes_amount") and hasattr(farm, "grapes_capacity"):
                try:
                    if int(farm.grapes_amount()) >= int(farm.grapes_capacity()):
                        worker.state = (
                            "working_field" if now_ms >= FARMER_NO_TARGET_WORKING_STATE_MS else "resting"
                        )
                        worker.camp_wait_until_ms = now_ms + 1_000
                        self._try_blocked_cycle_hunger(worker, now_ms)
                        return
                except (TypeError, ValueError):
                    pass
            plot = self.select_ripe_vineyard_for_vineyard_farm(farm, claimer=worker)
            if plot is None:
                worker.state = "working_field" if now_ms >= FARMER_NO_TARGET_WORKING_STATE_MS else "resting"
                worker.camp_wait_until_ms = now_ms + 1_000
                self._try_blocked_cycle_hunger(worker, now_ms)
                return
            if not self._reserve_vineyard_plot(plot, worker):
                worker.state = "working_field" if now_ms >= FARMER_NO_TARGET_WORKING_STATE_MS else "resting"
                worker.camp_wait_until_ms = now_ms + 1_000
                self._try_blocked_cycle_hunger(worker, now_ms)
                return
            if not self._start_farmer_move_to_vineyard(worker, plot, now_ms, world):
                self._release_vineyard_plot_reservations_for(worker)
                worker.state = "working_field" if now_ms >= FARMER_NO_TARGET_WORKING_STATE_MS else "resting"
                worker.camp_wait_until_ms = now_ms + 1_000
                self._try_blocked_cycle_hunger(worker, now_ms)
                return
            worker.state = "going_to_vineyard"
            worker.target_tree = plot.grid_pos
            worker.camp_wait_until_ms = 0
            return
        if worker.state == "working_field":
            self._park_worker_inside_building(worker, farm)
            if now_ms < worker.camp_wait_until_ms:
                return
            worker.state = "resting"
            worker.camp_wait_until_ms = now_ms
            return
        if worker.state == "arrived_vineyard":
            worker.state = "harvesting_grapes"
            worker.chop_started_ms = now_ms
            worker.chop_duration_ms = worker_building_action_ms(farm.type_tag)
            return
        if worker.state == "harvesting_grapes":
            if now_ms - worker.chop_started_ms < worker.chop_duration_ms:
                return
            worker.state = "vineyard_harvest_anim_done"
            return
        if worker.state == "arrived_camp":
            self._park_worker_inside_building(worker, farm)
            if worker.carrying == "grapes":
                try:
                    farm.add_grapes_to_storage(1)  # type: ignore[attr-defined]
                except (TypeError, ValueError):
                    pass
            worker.carrying = None
            worker.target_tree = None
            worker.chop_started_ms = 0
            worker.chop_duration_ms = CHOP_DURATION_MS
            worker.state = "resting"
            worker.camp_wait_until_ms = now_ms + worker_building_rest_ms(farm.type_tag)
            if self._registry is not None and world is not None:
                try_hunger_canteen_after_completed_cycle(
                    worker,
                    world=world,
                    registry=self._registry,
                    worker_manager=self,
                    now_ms=int(now_ms),
                )
            return

    def _complete_vineyard_farm_harvest(self, worker: Worker, farm: Building, now_ms: int, world: Any) -> None:
        """After harvest animation: store one grape unit if possible, reset plot, release reservation."""
        tile = worker.target_tree
        plot: Vineyard | None = None
        if tile is not None and self._registry is not None:
            hit = self._registry.at(int(tile[0]), int(tile[1]))
            if isinstance(hit, Vineyard):
                plot = hit
        if plot is None or not plot.is_ripe():
            self._release_vineyard_plot_reservations_for(worker)
            worker.target_tree = None
            worker.chop_started_ms = 0
            worker.chop_duration_ms = CHOP_DURATION_MS
            if not self._start_return_to_camp(worker, now_ms):
                worker.state = "vineyard_return_path_blocked"
                worker.camp_wait_until_ms = now_ms + 1_000
            return
        try:
            if int(farm.grapes_amount()) >= int(farm.grapes_capacity()):  # type: ignore[attr-defined]
                raise ValueError("grape storage full")
        except (TypeError, ValueError):
            self._release_vineyard_plot_reservations_for(worker)
            worker.target_tree = None
            worker.chop_started_ms = 0
            worker.chop_duration_ms = CHOP_DURATION_MS
            if not self._start_return_to_camp(worker, now_ms):
                worker.state = "vineyard_return_path_blocked"
                worker.camp_wait_until_ms = now_ms + 1_000
            return
        plot.mark_harvested(now_ms=now_ms)
        self._release_vineyard_plot_reservations_for(worker)
        worker.chop_started_ms = 0
        worker.chop_duration_ms = CHOP_DURATION_MS
        worker.carrying = "grapes"
        if not self._start_return_to_camp(worker, now_ms):
            worker.state = "vineyard_return_path_blocked"
            worker.camp_wait_until_ms = now_ms + 1_000

    def _builder_destination_tiles(self, building: Building) -> list[tuple[int, int]]:
        """Builder path target tiles for construction entry."""
        if building.type_tag == "FIELD" and building.grid_pos is not None:
            return [building.grid_pos]
        return self._approach_tiles(building)

    def _select_farmer_target_field(self, farm: Building) -> Building | None:
        if self._registry is None:
            return None
        storage_full = bool(hasattr(farm, "is_storage_full") and farm.is_storage_full())
        farm_home = building_center_tile(farm)
        phases: dict[tuple[int, int], str] = {}
        tile_to_field: dict[tuple[int, int], Building] = {}
        for building in self._registry.all():
            if building.type_tag != "FIELD":
                continue
            if building.is_under_construction or building.grid_pos is None:
                continue
            tile = (int(building.grid_pos[0]), int(building.grid_pos[1]))
            if self._is_field_reserved_by_other(tile, None):
                continue
            tile_to_field[tile] = building
            phase = self._read_field_phase(building, tile=tile)
            if storage_full and phase == WHEAT_PHASE_4:
                # Block new harvest dispatch while farm local storage is full.
                continue
            phases[tile] = phase
        selected_tile = select_farmer_field_target(
            farm_home=farm_home,
            field_phases=phases,
            max_radius=FARMER_FIELD_RADIUS,
        )
        if selected_tile is None:
            return None
        return tile_to_field.get(selected_tile)

    def _farm_has_actionable_field(self, farm: Building) -> bool:
        if self._registry is None:
            return False
        farm_home = building_center_tile(farm)
        for building in self._registry.all():
            if building.type_tag != "FIELD" or building.is_under_construction or building.grid_pos is None:
                continue
            tile = (int(building.grid_pos[0]), int(building.grid_pos[1]))
            if self._is_field_reserved_by_other(tile, None):
                continue
            if max(abs(tile[0] - farm_home[0]), abs(tile[1] - farm_home[1])) > FARMER_FIELD_RADIUS:
                continue
            phase = self._read_field_phase(building, tile=tile)
            if phase in {WHEAT_EMPTY, WHEAT_PHASE_4}:
                return True
        return False

    def _read_field_phase(self, field: Building, *, tile: tuple[int, int] | None = None) -> str:
        if isinstance(field, Field):
            return str(field.wheat_phase).upper()
        pos = tile if tile is not None else field.grid_pos
        if pos is not None:
            return WHEAT_EMPTY
        return WHEAT_EMPTY

    def _write_field_phase(self, field: Building, phase: str) -> None:
        if isinstance(field, Field):
            field.set_wheat_phase(phase, now_ms=int(self._now_ms_fn()))

    def _reserve_field(self, field: Building, worker: Worker) -> bool:
        if field.grid_pos is None:
            return False
        tile = (int(field.grid_pos[0]), int(field.grid_pos[1]))
        owner = self._field_reservations.get(tile)
        if owner is None or owner is worker:
            self._field_reservations[tile] = worker
            return True
        return False

    def _release_field_reservations_for(self, worker: Worker) -> None:
        reserved = [tile for tile, owner in self._field_reservations.items() if owner is worker]
        for tile in reserved:
            self._field_reservations.pop(tile, None)

    def _is_field_reserved_by_other(self, tile: tuple[int, int], worker: Worker | None) -> bool:
        owner = self._field_reservations.get((int(tile[0]), int(tile[1])))
        return owner is not None and owner is not worker

    def _excluded_vineyard_tiles_for_claimer(self, claimer: Worker | None) -> set[tuple[int, int]]:
        if claimer is None:
            return set(self._vineyard_plot_reservations.keys())
        return {t for t, w in self._vineyard_plot_reservations.items() if w is not claimer}

    def select_ripe_vineyard_for_vineyard_farm(
        self, farm: Building, *, claimer: Worker | None
    ) -> Vineyard | None:
        """Pick the nearest ripe ``VINEYARD`` in this farm's harvest radius, excluding other workers' claims."""
        if self._registry is None:
            return None
        if farm.type_tag != "VINEYARD_FARM" or farm.is_under_construction or farm.grid_pos is None:
            return None
        if not hasattr(farm, "harvest_radius_cells"):
            return None
        home = building_center_tile(farm)
        radius = int(farm.harvest_radius_cells())
        ripe_tiles: list[tuple[int, int]] = []
        for b in self._registry.all():
            if not isinstance(b, Vineyard):
                continue
            if b.is_under_construction or not b.is_ripe() or b.grid_pos is None:
                continue
            ripe_tiles.append((int(b.grid_pos[0]), int(b.grid_pos[1])))
        excluded = self._excluded_vineyard_tiles_for_claimer(claimer)
        chosen = select_ripe_vineyard_target_tile(
            farm_home=home,
            ripe_tiles=ripe_tiles,
            excluded_tiles=excluded,
            max_radius=radius,
        )
        if chosen is None:
            return None
        hit = self._registry.at(chosen[0], chosen[1])
        return hit if isinstance(hit, Vineyard) else None

    def _vineyard_farm_has_actionable_ripe(self, farm: Building) -> bool:
        """Whether an unreserved ripe vineyard exists in harvest radius (for panel copy)."""
        return farm.type_tag == "VINEYARD_FARM" and self.select_ripe_vineyard_for_vineyard_farm(
            farm, claimer=None
        ) is not None

    def _reserve_vineyard_plot(self, plot: Building, worker: Worker) -> bool:
        if not isinstance(plot, Vineyard) or plot.grid_pos is None:
            return False
        tile = (int(plot.grid_pos[0]), int(plot.grid_pos[1]))
        owner = self._vineyard_plot_reservations.get(tile)
        if owner is None or owner is worker:
            self._vineyard_plot_reservations[tile] = worker
            return True
        return False

    def _release_vineyard_plot_reservations_for(self, worker: Worker) -> None:
        reserved = [t for t, w in self._vineyard_plot_reservations.items() if w is worker]
        for tile in reserved:
            self._vineyard_plot_reservations.pop(tile, None)

    def _is_vineyard_plot_reserved_by_other(self, tile: tuple[int, int], worker: Worker | None) -> bool:
        owner = self._vineyard_plot_reservations.get((int(tile[0]), int(tile[1])))
        return owner is not None and owner is not worker

    def _update_field_growth(self, now_ms: int) -> None:
        if self._registry is None:
            return
        for building in self._registry.all():
            if isinstance(building, Field) and not building.is_under_construction:
                building.update_wheat_growth(now_ms)
            elif isinstance(building, Vineyard):
                building.tick_growth(now_ms=int(now_ms))

    def _field_at(self, tile: tuple[int, int]) -> Building | None:
        if self._registry is None:
            return None
        for building in self._registry.all():
            if building.type_tag != "FIELD":
                continue
            if building.grid_pos is None:
                continue
            if tuple(building.grid_pos) == tuple(tile):
                return building
        return None

    @staticmethod
    def _start_farmer_move_to_field(worker: Worker, field: Building, now_ms: int, world: Any) -> bool:
        if field.grid_pos is None:
            return False
        blocked = world.blocked_tiles()
        blocked.discard(worker.current_tile)
        path = find_path_bfs(world, worker.current_tile, field.grid_pos, blocked)
        if path is None:
            return False
        worker.start_move(path, started_ms=now_ms, move_state="going_to_field")
        return True

    @staticmethod
    def _start_farmer_move_to_vineyard(worker: Worker, plot: Vineyard, now_ms: int, world: Any) -> bool:
        """Route directly onto the passable vineyard plot tile."""
        if plot.grid_pos is None:
            return False
        blocked = world.blocked_tiles()
        blocked.discard(worker.current_tile)
        goal = (int(plot.grid_pos[0]), int(plot.grid_pos[1]))
        path = find_path_bfs(world, worker.current_tile, goal, blocked)
        if path is None:
            return False
        worker.start_move(path, started_ms=now_ms, move_state="going_to_vineyard")
        return True

