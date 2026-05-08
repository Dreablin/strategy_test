"""Bakery building: processes flour and water into bread."""

from __future__ import annotations

from typing import ClassVar

from game.buildings.base import Building
from game.config import building_level_int_setting


class Bakery(Building):
    type_tag: ClassVar[str] = "BAKERY"
    __slots__ = (
        "active",
        "flour_in",
        "water_in",
        "bread_out",
        "processing_started_ms",
        "processing_duration_ms",
    )

    def __init__(self, level: int = 1, grid_pos: tuple[int, int] | None = None) -> None:
        super().__init__(level=level, grid_pos=grid_pos)
        self.active = True
        self.flour_in = 0
        self.water_in = 0
        self.bread_out = 0
        self.processing_started_ms = 0
        self.processing_duration_ms = 45_000

    def set_active(self, value: bool) -> None:
        self.active = bool(value)

    def input_capacity(self) -> int:
        return self.storage_capacity()

    def output_capacity(self) -> int:
        return self.storage_capacity()

    def water_capacity(self) -> int:
        return self.storage_capacity()

    def storage_capacity(self) -> int:
        return building_level_int_setting(self.type_tag, "storage", self.level)

    def input_amount(self) -> int:
        return int(self.flour_in)

    def output_amount(self) -> int:
        return int(self.bread_out)

    def water_amount(self) -> int:
        return int(self.water_in)

    def has_recipe_inputs(self) -> bool:
        return self.flour_in > 0 and self.water_in > 0

    def add_flour_in(self, amount: int) -> None:
        n = int(amount)
        if n < 0:
            raise ValueError("amount must be non-negative")
        if self.flour_in + n > self.input_capacity():
            raise ValueError("flour input overflow")
        self.flour_in += n

    def take_flour_in(self, amount: int) -> None:
        n = int(amount)
        if n < 0:
            raise ValueError("amount must be non-negative")
        if n > self.flour_in:
            raise ValueError("insufficient flour input")
        self.flour_in -= n

    def add_water_in(self, amount: int) -> None:
        n = int(amount)
        if n < 0:
            raise ValueError("amount must be non-negative")
        if self.water_in + n > self.water_capacity():
            raise ValueError("water input overflow")
        self.water_in += n

    def take_water_in(self, amount: int) -> None:
        n = int(amount)
        if n < 0:
            raise ValueError("amount must be non-negative")
        if n > self.water_in:
            raise ValueError("insufficient water input")
        self.water_in -= n

    def add_bread_out(self, amount: int) -> None:
        n = int(amount)
        if n < 0:
            raise ValueError("amount must be non-negative")
        if self.bread_out + n > self.output_capacity():
            raise ValueError("bread output overflow")
        self.bread_out += n

    def take_bread_out(self, amount: int) -> None:
        n = int(amount)
        if n < 0:
            raise ValueError("amount must be non-negative")
        if n > self.bread_out:
            raise ValueError("insufficient bread output")
        self.bread_out -= n

    def processing_progress(self, now_ms: int) -> float:
        if self.processing_started_ms <= 0:
            return 0.0
        duration = max(1, int(self.processing_duration_ms))
        elapsed = max(0, int(now_ms) - int(self.processing_started_ms))
        return max(0.0, min(1.0, elapsed / float(duration)))

    def progress_state(self, now_ms: int) -> str:
        return "processing" if self.processing_started_ms > 0 and self.processing_progress(now_ms) < 1.0 else "idle"
