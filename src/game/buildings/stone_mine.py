"""Stone Mine — produces stone when staffed."""

from typing import ClassVar

from game.buildings.base import Building


class StoneMine(Building):
    type_tag: ClassVar[str] = "STONE_MINE"
    income_resource: ClassVar[str] = "stone"
