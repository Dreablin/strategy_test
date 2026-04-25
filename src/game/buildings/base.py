"""Shared building attributes: type tag, footprint, level bounds, and income."""

from typing import ClassVar

from game.config import MAX_LEVEL


class Building:
    """Subclasses set `type_tag`, `footprint`, and optionally `income_resource`."""

    type_tag: ClassVar[str] = ""
    footprint: ClassVar[tuple[int, int]] = (2, 2)
    income_resource: ClassVar[str | None] = None

    __slots__ = ("level", "grid_pos")

    def __init__(self, level: int = 1, grid_pos: tuple[int, int] | None = None) -> None:
        mx = type(self).max_level()
        if level < 1 or level > mx:
            raise ValueError(f"level must be between 1 and {mx} inclusive")
        self.level = level
        self.grid_pos = grid_pos

    @classmethod
    def max_level(cls) -> int:
        return MAX_LEVEL

    @classmethod
    def income(cls, level: int) -> dict[str, int]:
        key = cls.income_resource
        if key is None:
            return {}
        return {key: 5 * level}
