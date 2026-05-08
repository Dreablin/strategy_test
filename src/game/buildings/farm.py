"""Farm — produces wheat when staffed."""

from typing import ClassVar

from game.buildings.base import Building
from game.buildings.storage import StorageMixin
from game.config import building_level_int_setting


class Farm(StorageMixin, Building):
    type_tag: ClassVar[str] = "FARM"
    __slots__ = ("stored",)

    def __init__(self, level: int = 1, grid_pos: tuple[int, int] | None = None) -> None:
        super().__init__(level=level, grid_pos=grid_pos)
        self.stored = 0

    def storage_capacity(self) -> int:
        return building_level_int_setting(self.type_tag, "storage", self.level)
