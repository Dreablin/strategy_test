"""Winery building: processes grapes into wine."""

from __future__ import annotations

from typing import ClassVar

from game.buildings.base import Building
from game.config import building_int_setting, building_level_int_setting


class Winery(Building):
    type_tag: ClassVar[str] = "WINERY"
    footprint: ClassVar[tuple[int, int]] = (2, 2)
    __slots__ = (
        "active",
        "grapes_in",
        "wine_out",
        "processing_started_ms",
        "processing_duration_ms",
    )

    def __init__(self, level: int = 1, grid_pos: tuple[int, int] | None = None) -> None:
        super().__init__(level=level, grid_pos=grid_pos)
        self.active = True
        self.grapes_in = 0
        self.wine_out = 0
        self.processing_started_ms = 0
        self.processing_duration_ms = 0

    def set_active(self, value: bool) -> None:
        self.active = bool(value)

    def input_capacity(self) -> int:
        return building_level_int_setting(self.type_tag, "input_storage", self.level)

    def output_capacity(self) -> int:
        return building_level_int_setting(self.type_tag, "output_storage", self.level)

    def input_amount(self) -> int:
        return int(self.grapes_in)

    def output_amount(self) -> int:
        return int(self.wine_out)

    def add_grapes(self, amount: int) -> None:
        n = int(amount)
        if n < 0:
            raise ValueError("amount must be non-negative")
        if self.grapes_in + n > self.input_capacity():
            raise ValueError("grapes input overflow")
        self.grapes_in += n

    def take_grapes(self, amount: int) -> None:
        n = int(amount)
        if n < 0:
            raise ValueError("amount must be non-negative")
        if n > self.grapes_in:
            raise ValueError("insufficient grapes")
        self.grapes_in -= n

    def add_wine(self, amount: int) -> None:
        n = int(amount)
        if n < 0:
            raise ValueError("amount must be non-negative")
        if self.wine_out + n > self.output_capacity():
            raise ValueError("wine output overflow")
        self.wine_out += n

    def take_wine(self, amount: int) -> None:
        n = int(amount)
        if n < 0:
            raise ValueError("amount must be non-negative")
        if n > self.wine_out:
            raise ValueError("insufficient wine")
        self.wine_out -= n

    def recipe_input_count(self) -> int:
        return int(building_int_setting(self.type_tag, "recipe", "input", "grapes"))

    def recipe_output_count(self) -> int:
        return int(building_int_setting(self.type_tag, "recipe", "output", "wine"))

    def cycle_ms(self) -> int:
        return building_int_setting(self.type_tag, "production", "cycle_ms")

    def rest_ms(self) -> int:
        return building_int_setting(self.type_tag, "production", "rest_ms")

    def has_recipe_inputs(self) -> bool:
        return self.grapes_in >= self.recipe_input_count()

    def has_output_space(self) -> bool:
        return self.wine_out + self.recipe_output_count() <= self.output_capacity()

    def processing_progress(self, now_ms: int) -> float:
        if self.processing_started_ms <= 0:
            return 0.0
        duration = max(1, self.cycle_ms())
        elapsed = max(0, int(now_ms) - int(self.processing_started_ms))
        return max(0.0, min(1.0, elapsed / float(duration)))

    def progress_state(self, now_ms: int) -> str:
        if self.processing_started_ms > 0 and self.processing_progress(now_ms) < 1.0:
            return "processing"
        return "idle"

    @classmethod
    def max_level(cls) -> int:
        return 10
