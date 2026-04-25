"""Lumber Camp — produces wood when staffed."""

from typing import ClassVar

from game.buildings.base import Building


class LumberCamp(Building):
    type_tag: ClassVar[str] = "LUMBER_CAMP"
    income_resource: ClassVar[str] = "wood"
