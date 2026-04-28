"""Forester Hut building with active toggle and fixed level cap."""

from typing import ClassVar

from game.buildings.base import Building


class ForesterHut(Building):
    type_tag: ClassVar[str] = "FORESTER_HUT"
    footprint: ClassVar[tuple[int, int]] = (2, 2)
    __slots__ = ("active",)

    def __init__(self, level: int = 1, grid_pos: tuple[int, int] | None = None) -> None:
        super().__init__(level=level, grid_pos=grid_pos)
        self.active = True

    @classmethod
    def max_level(cls) -> int:
        return 1

    def set_active(self, value: bool) -> None:
        self.active = bool(value)
