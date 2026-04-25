"""Town Hall — fixed level 1, no production income."""

from typing import ClassVar

from game.buildings.base import Building


class TownHall(Building):
    type_tag: ClassVar[str] = "TOWN_HALL"
    footprint: ClassVar[tuple[int, int]] = (3, 3)

    @classmethod
    def max_level(cls) -> int:
        return 1
