"""Field building type used for wheat growth cycles."""

from __future__ import annotations

from typing import ClassVar

from game.buildings.base import Building


class Field(Building):
    type_tag: ClassVar[str] = "FIELD"
    footprint: ClassVar[tuple[int, int]] = (1, 1)

    @classmethod
    def max_level(cls) -> int:
        return 1
