"""Farm — produces food when staffed."""

from typing import ClassVar

from game.buildings.base import Building
from game.buildings.storage import StorageMixin


class Farm(StorageMixin, Building):
    type_tag: ClassVar[str] = "FARM"
    income_resource: ClassVar[str] = "food"
    __slots__ = ("stored",)

    def __init__(self, level: int = 1, grid_pos: tuple[int, int] | None = None) -> None:
        super().__init__(level=level, grid_pos=grid_pos)
        self.stored = 0
