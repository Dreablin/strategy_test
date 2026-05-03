"""Well building: direct water source for carriers."""

from __future__ import annotations

from typing import ClassVar

from game.buildings.base import Building


class Well(Building):
    type_tag: ClassVar[str] = "WELL"
    footprint: ClassVar[tuple[int, int]] = (1, 1)
    __slots__ = ("busy",)

    def __init__(self, level: int = 1, grid_pos: tuple[int, int] | None = None) -> None:
        super().__init__(level=level, grid_pos=grid_pos)
        self.busy = False

    @classmethod
    def max_level(cls) -> int:
        return 1

    def reserve(self) -> None:
        if self.busy:
            raise ValueError("well is busy")
        self.busy = True

    def release(self) -> None:
        self.busy = False
