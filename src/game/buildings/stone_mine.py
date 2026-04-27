"""Stone Mine — produces stone when staffed."""

from typing import ClassVar

from game.buildings.base import Building
from game.buildings.storage import StorageMixin


class StoneMine(StorageMixin, Building):
    type_tag: ClassVar[str] = "STONE_MINE"
    __slots__ = ("stored", "active", "delivered_stone")

    def __init__(self, level: int = 1, grid_pos: tuple[int, int] | None = None) -> None:
        super().__init__(level=level, grid_pos=grid_pos)
        self.stored = 0
        self.active = True
        self.delivered_stone = 0

    def set_active(self, value: bool) -> None:
        self.active = bool(value)

    def record_stone_delivered(self, amount: int = 1) -> None:
        if amount < 0:
            raise ValueError("amount must be non-negative")
        self.delivered_stone += amount
