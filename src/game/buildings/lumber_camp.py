"""Lumber Camp state for active chop cycle and delivered-wood counter."""

from typing import ClassVar

from game.buildings.base import Building
from game.buildings.storage import StorageMixin


class LumberCamp(StorageMixin, Building):
    type_tag: ClassVar[str] = "LUMBER_CAMP"
    income_resource: ClassVar[str] = None
    __slots__ = ("active", "delivered_wood", "stored")

    def __init__(self, level: int = 1, grid_pos: tuple[int, int] | None = None) -> None:
        super().__init__(level=level, grid_pos=grid_pos)
        self.active = True
        self.delivered_wood = 0
        self.stored = 0

    def set_active(self, value: bool) -> None:
        self.active = bool(value)

    def record_wood_delivered(self, amount: int = 1) -> None:
        if amount < 0:
            raise ValueError("amount must be non-negative")
        self.delivered_wood += amount
