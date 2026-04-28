"""School building used to hire workers."""

from typing import ClassVar

from game.buildings.base import Building


class School(Building):
    type_tag: ClassVar[str] = "SCHOOL"
    footprint: ClassVar[tuple[int, int]] = (2, 2)

    @classmethod
    def max_level(cls) -> int:
        return 1
