"""Iron Mine — produces iron when staffed."""

from typing import ClassVar

from game.buildings.base import Building


class IronMine(Building):
    type_tag: ClassVar[str] = "IRON_MINE"
    income_resource: ClassVar[str] = "iron"
