"""House social building that contributes housing capacity."""

from typing import ClassVar

from game.buildings.base import Building


class House(Building):
    type_tag: ClassVar[str] = "HOUSE"
    footprint: ClassVar[tuple[int, int]] = (2, 2)
