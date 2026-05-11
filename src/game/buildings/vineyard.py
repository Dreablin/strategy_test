"""Vineyard plot: 1×1 tile; growth timing from ``vineyard.json`` (runtime in later tasks)."""

from __future__ import annotations

from typing import ClassVar

from game.buildings.base import Building
from game.config import building_int_setting


class Vineyard(Building):
    type_tag: ClassVar[str] = "VINEYARD"
    footprint: ClassVar[tuple[int, int]] = (1, 1)
    __slots__ = ("growth_stage", "growth_last_change_ms")

    def __init__(self, level: int = 1, grid_pos: tuple[int, int] | None = None) -> None:
        super().__init__(level=level, grid_pos=grid_pos)
        self.growth_stage = 0
        self.growth_last_change_ms = 0

    def growth_stage_count(self) -> int:
        return building_int_setting(self.type_tag, "growth", "stage_count")

    def stage_duration_ms(self) -> int:
        return building_int_setting(self.type_tag, "growth", "stage_duration_ms")

    def growth_stage_index(self) -> int:
        """Current maturation stage (0 = not started; 1..N while growing; N when ripe)."""
        return int(self.growth_stage)

    def set_growth_stage(self, stage: int, *, now_ms: int | None = None) -> None:
        n = int(stage)
        cap = self.growth_stage_count()
        if n < 0 or n > cap:
            raise ValueError("growth stage out of range")
        self.growth_stage = n
        if now_ms is not None:
            self.growth_last_change_ms = int(now_ms)

    def is_ripe(self) -> bool:
        return self.growth_stage_index() >= self.growth_stage_count() and self.growth_stage_count() > 0

    def reset_growth_after_harvest(self, *, now_ms: int) -> None:
        """Return to an idle plot; automatic regrowth is wired in T326+."""
        self.growth_stage = 0
        self.growth_last_change_ms = int(now_ms)
