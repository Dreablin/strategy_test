"""Iron Mine — produces iron when staffed."""

from typing import ClassVar

from game.buildings.base import Building
from game.buildings.storage import StorageMixin


class IronMine(StorageMixin, Building):
    type_tag: ClassVar[str] = "IRON_MINE"
    income_resource: ClassVar[str] = "iron"
    __slots__ = ("stored",)

    def __init__(self, level: int = 1, grid_pos: tuple[int, int] | None = None) -> None:
        super().__init__(level=level, grid_pos=grid_pos)
        self.stored = 0
