"""Farm — produces food when staffed."""

from typing import ClassVar

from game.buildings.base import Building


class Farm(Building):
    type_tag: ClassVar[str] = "FARM"
    income_resource: ClassVar[str] = "food"
