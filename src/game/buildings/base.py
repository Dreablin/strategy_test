"""Shared building attributes: type tag, footprint, level bounds, and income."""

from __future__ import annotations

from typing import ClassVar

from game.construction import ConstructionSite
from game.config import MAX_LEVEL


class Building:
    """Subclasses set `type_tag` and `footprint`."""

    type_tag: ClassVar[str] = ""
    footprint: ClassVar[tuple[int, int]] = (2, 2)

    __slots__ = ("level", "grid_pos", "construction_site")

    def __init__(self, level: int = 1, grid_pos: tuple[int, int] | None = None) -> None:
        mx = type(self).max_level()
        if level < 1 or level > mx:
            raise ValueError(f"level must be between 1 and {mx} inclusive")
        self.level = level
        self.grid_pos = grid_pos
        self.construction_site: ConstructionSite | None = None

    @property
    def is_under_construction(self) -> bool:
        return self.construction_site is not None

    @classmethod
    def max_level(cls) -> int:
        return MAX_LEVEL

    @classmethod
    def income(cls, level: int) -> dict[str, int]:
        """Passive income was removed; resources come from worker deposit cycles."""
        _ = level
        return {}
