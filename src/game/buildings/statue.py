"""Mission statue building with four named construction stages."""

from __future__ import annotations

from typing import ClassVar

from game.buildings.base import Building
from game import i18n


class Statue(Building):
    type_tag: ClassVar[str] = "STATUE"
    footprint: ClassVar[tuple[int, int]] = (3, 3)
    __slots__ = ("construction_deliveries_enabled",)

    def __init__(self, level: int = 1, grid_pos: tuple[int, int] | None = None) -> None:
        super().__init__(level=level, grid_pos=grid_pos)
        self.construction_deliveries_enabled = True

    @classmethod
    def max_level(cls) -> int:
        return 4

    def set_construction_deliveries_enabled(self, value: bool) -> None:
        self.construction_deliveries_enabled = bool(value)

    def stage_name(self, level: int | None = None) -> str:
        stage_level = int(self.level if level is None else level)
        key = f"statue.stage.{stage_level}"
        localized = i18n.t(key)
        if localized != key:
            return localized
        return f"Stage {stage_level}"

    def next_stage_name(self) -> str | None:
        if self.level >= self.max_level():
            return None
        return self.stage_name(self.level + 1)

    def current_construction_stage_name(self) -> str:
        site = self.construction_site
        if site is None:
            return self.stage_name()
        return self.stage_name(int(site.target_level))

    @property
    def mission_complete(self) -> bool:
        return self.level >= self.max_level() and not self.is_under_construction
