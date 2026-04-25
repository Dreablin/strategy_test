"""Shared building attributes: type tag, footprint, level bounds, and income."""

from typing import ClassVar

from game.config import MAX_LEVEL


class Building:
    """Subclasses set `type_tag`, `footprint`, and optionally `income_resource`."""

    type_tag: ClassVar[str] = ""
    footprint: ClassVar[tuple[int, int]] = (2, 2)
    income_resource: ClassVar[str | None] = None

    __slots__ = ("level",)

    def __init__(self, level: int = 1) -> None:
        mx = type(self).max_level()
        if level < 1 or level > mx:
            raise ValueError(f"level must be between 1 and {mx} inclusive")
        self.level = level

    @classmethod
    def max_level(cls) -> int:
        return MAX_LEVEL

    @classmethod
    def income(cls, level: int) -> dict[str, int]:
        key = cls.income_resource
        if key is None:
            return {}
        return {key: 5 * level}
