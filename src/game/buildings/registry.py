"""Placement registry: validates rules, tracks buildings, syncs world occupancy."""

from __future__ import annotations

import math
from typing import Type

from game.buildings.base import Building
from game.world import World


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

    __slots__ = ("_buildings", "_world")

    def __init__(self, world: World) -> None:
        self._world = world
        self._buildings: list[Building] = []

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
        sep_need = math.ceil(0.5 * max(w, h))
        for b in self._buildings:
            pos = b.grid_pos
            if pos is None:
                continue
            bx, by = pos
            bw, bh = type(b).footprint
            if _min_chebyshev_between_footprints(gx, gy, w, h, bx, by, bw, bh) < sep_need:
                return False
        return True

    def place(self, cls: Type[Building], grid_pos: tuple[int, int]) -> Building:
        if not self.can_place(cls, grid_pos):
            raise ValueError("invalid placement")
        gx, gy = grid_pos
        w, h = cls.footprint
        inst = cls(level=1, grid_pos=grid_pos)
        self._world.mark_occupied(gx, gy, w, h)
        self._buildings.append(inst)
        return inst

    def demolish(self, building: Building) -> None:
        if building not in self._buildings:
            raise ValueError("unknown building")
        pos = building.grid_pos
        if pos is None:
            raise ValueError("building has no grid position")
        gx, gy = pos
        w, h = type(building).footprint
        self._world.free(gx, gy, w, h)
        self._buildings.remove(building)

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
