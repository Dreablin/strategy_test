"""Sawmill building scaffold for Phase 20."""

from __future__ import annotations

from typing import ClassVar

from game.buildings.base import Building


class Sawmill(Building):
    type_tag: ClassVar[str] = "SAWMILL"
    __slots__ = ("active",)

    def __init__(self, level: int = 1, grid_pos: tuple[int, int] | None = None) -> None:
        super().__init__(level=level, grid_pos=grid_pos)
        self.active = True

    def set_active(self, value: bool) -> None:
        self.active = bool(value)
