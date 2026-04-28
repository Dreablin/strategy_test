"""Placement registry: validates rules, tracks buildings, syncs world occupancy."""

from __future__ import annotations

from collections.abc import Collection
from typing import Type

from game.buildings.base import Building
from game.buildings.costs import upgrade_cost
from game.config import TOWN_HALL_MIN_LEVEL_FOR_BUILDING
from game.housing import housing_house, max_population
from game.resources import ResourceManager
from game.world import World
from game.workers import WorkerManager


def _min_chebyshev_between_footprints(
    ax: int, ay: int, aw: int, ah: int, bx: int, by: int, bw: int, bh: int
) -> int:
    best = 10**9
    for gx in range(ax, ax + aw):
        for gy in range(ay, ay + ah):
            for gx2 in range(bx, bx + bw):
                for gy2 in range(by, by + bh):
                    d = max(abs(gx - gx2), abs(gy - gy2))
                    best = min(best, d)
    return best


class BuildingRegistry:
    """Owns placed `Building` instances and mirrors their footprints on `World`."""

    __slots__ = ("_buildings", "_world", "_worker_manager")

    def __init__(self, world: World) -> None:
        self._world = world
        self._buildings: list[Building] = []
        self._worker_manager: WorkerManager | None = None

    def bind_worker_manager(self, worker_manager: WorkerManager) -> None:
        """Attach worker manager callbacks for upgrade-driven bonus refresh."""
        self._worker_manager = worker_manager

    def all(self) -> list[Building]:
        return list(self._buildings)

    def at(self, gx: int, gy: int) -> Building | None:
        for b in self._buildings:
            pos = b.grid_pos
            if pos is None:
                continue
            bx, by = pos
            w, h = type(b).footprint
            if bx <= gx < bx + w and by <= gy < by + h:
                return b
        return None

    def can_place(self, cls: Type[Building], grid_pos: tuple[int, int]) -> bool:
        # Tech gates by Town Hall level.
        th_level = self.town_hall_level()
        required = TOWN_HALL_MIN_LEVEL_FOR_BUILDING.get(cls.type_tag)
        if required is not None and th_level < required:
            return False

        gx, gy = grid_pos
        w, h = cls.footprint
        if not self._footprint_inside_grass(gx, gy, w, h):
            return False
        if cls.type_tag == "TOWN_HALL" and any(
            b.type_tag == "TOWN_HALL" for b in self._buildings
        ):
            return False
        if self._world_footprint_overlaps_occupied(gx, gy, w, h):
            return False
        if self._world_footprint_overlaps_stones(gx, gy, w, h):
            return False
        # Require at least one empty tile between any two footprints.
        min_allowed = 2
        for b in self._buildings:
            pos = b.grid_pos
            if pos is None:
                continue
            bx, by = pos
            bw, bh = type(b).footprint
            if _min_chebyshev_between_footprints(gx, gy, w, h, bx, by, bw, bh) < min_allowed:
                return False
        return True

    def town_hall_level(self) -> int:
        """Current Town Hall level (0 if none placed)."""
        for building in self._buildings:
            if building.type_tag == "TOWN_HALL":
                return building.level
        return 0

    def place(self, cls: Type[Building], grid_pos: tuple[int, int]) -> Building:
        if not self.can_place(cls, grid_pos):
            raise ValueError("invalid placement")
        gx, gy = grid_pos
        w, h = cls.footprint
        for ty in range(gy, gy + h):
            for tx in range(gx, gx + w):
                self._world.remove_tree(tx, ty)
        inst = cls(level=1, grid_pos=grid_pos)
        self._world.mark_occupied(gx, gy, w, h)
        self._buildings.append(inst)
        return inst

    def demolish(self, building: Building, worker_manager: WorkerManager | None = None) -> None:
        if building not in self._buildings:
            raise ValueError("unknown building")
        if building.type_tag == "HOUSE":
            wm = worker_manager or self._worker_manager
            current_population = len(wm.workers()) if wm is not None else 0
            current_cap = max_population(self, wm or current_population)
            next_cap = current_cap - housing_house(building.level)
            if current_population > next_cap:
                return
        if worker_manager is not None:
            worker_manager.notify_demolished(building)
        pos = building.grid_pos
        if pos is None:
            raise ValueError("building has no grid position")
        gx, gy = pos
        w, h = type(building).footprint
        self._world.free(gx, gy, w, h)
        self._buildings.remove(building)

    def sync_resources_per_cycle(
        self,
        resources: ResourceManager,
        *,
        staffed_buildings: Collection[Building] = (),
    ) -> None:
        """Set per-cycle preview totals.

        Passive production is removed globally; all resources are delivered by workers
        via explicit gather/deposit cycles. Keep this API to avoid touching callers.
        """
        _ = staffed_buildings
        resources.set_per_cycle_totals({"food": 0, "wood": 0, "stone": 0, "iron": 0})

    def upgrade_building(self, building: Building, resources: ResourceManager) -> bool:
        """Spend ``upgrade_cost(level)``, increment ``level``, refresh per-cycle totals. Returns success."""
        if building not in self._buildings:
            return False
        cls = type(building)
        if building.level >= cls.max_level():
            return False
        try:
            cost = upgrade_cost(building.type_tag, building.level)
        except ValueError:
            return False
        if not resources.try_spend(cost):
            return False
        building.level += 1
        if self._worker_manager is not None:
            self._worker_manager.refresh_building_bonuses(building)
        self.sync_resources_per_cycle(resources, staffed_buildings=())
        return True

    def _footprint_inside_grass(self, gx: int, gy: int, w: int, h: int) -> bool:
        for ty in range(gy, gy + h):
            for tx in range(gx, gx + w):
                if not self._world.is_in_grass(tx, ty):
                    return False
        return True

    def _world_footprint_overlaps_occupied(self, gx: int, gy: int, w: int, h: int) -> bool:
        for ty in range(gy, gy + h):
            for tx in range(gx, gx + w):
                if self._world.is_occupied(tx, ty):
                    return True
        return False

    def _world_footprint_overlaps_stones(self, gx: int, gy: int, w: int, h: int) -> bool:
        for ty in range(gy, gy + h):
            for tx in range(gx, gx + w):
                if self._world.is_stone_blocking(tx, ty):
                    return True
        return False
