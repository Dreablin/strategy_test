"""Vineyard Farm — local grape storage; harvest and growth wiring come in later tasks."""

from __future__ import annotations

from typing import ClassVar

from game.buildings.base import Building
from game.config import building_int_setting, building_level_int_setting


class VineyardFarm(Building):
    type_tag: ClassVar[str] = "VINEYARD_FARM"
    footprint: ClassVar[tuple[int, int]] = (2, 2)
    __slots__ = ("active", "grapes_in")

    def __init__(self, level: int = 1, grid_pos: tuple[int, int] | None = None) -> None:
        super().__init__(level=level, grid_pos=grid_pos)
        self.active = True
        self.grapes_in = 0

    def set_active(self, value: bool) -> None:
        self.active = bool(value)

    def storage_capacity(self) -> int:
        return building_level_int_setting(self.type_tag, "storage", self.level)

    def harvest_radius_cells(self) -> int:
        return building_int_setting(self.type_tag, "harvest", "radius_cells")

    def grapes_amount(self) -> int:
        return int(self.grapes_in)

    def grapes_capacity(self) -> int:
        return self.storage_capacity()

    def add_grapes_to_storage(self, amount: int) -> None:
        n = int(amount)
        if n < 0:
            raise ValueError("amount must be non-negative")
        if self.grapes_in + n > self.grapes_capacity():
            raise ValueError("grape storage overflow")
        self.grapes_in += n

    def take_grapes_from_storage(self, amount: int) -> None:
        n = int(amount)
        if n < 0:
            raise ValueError("amount must be non-negative")
        if n > self.grapes_in:
            raise ValueError("insufficient grapes in storage")
        self.grapes_in -= n
