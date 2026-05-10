"""Cow farm: beef + hide processor; wheat/water/beef/hide slots gain helpers across tasks."""

from __future__ import annotations

from typing import ClassVar

from game.buildings.base import Building
from game.config import building_int_setting, building_level_int_setting


class CowFarm(Building):
    type_tag: ClassVar[str] = "COW_FARM"
    footprint: ClassVar[tuple[int, int]] = (2, 2)
    __slots__ = (
        "active",
        "wheat_in",
        "water_in",
        "beef_out",
        "hide_out",
        "processing_started_ms",
        "processing_duration_ms",
    )

    def __init__(self, level: int = 1, grid_pos: tuple[int, int] | None = None) -> None:
        super().__init__(level=level, grid_pos=grid_pos)
        self.active = True
        self.wheat_in = 0
        self.water_in = 0
        self.beef_out = 0
        self.hide_out = 0
        self.processing_started_ms = 0
        self.processing_duration_ms = building_int_setting(self.type_tag, "production", "cycle_ms")

    def set_active(self, value: bool) -> None:
        self.active = bool(value)

    def storage_capacity(self) -> int:
        return building_level_int_setting(self.type_tag, "storage", self.level)

    def wheat_amount(self) -> int:
        return int(self.wheat_in)

    def wheat_capacity(self) -> int:
        return self.storage_capacity()

    def add_wheat_in(self, amount: int) -> None:
        n = int(amount)
        if n < 0:
            raise ValueError("amount must be non-negative")
        if self.wheat_in + n > self.wheat_capacity():
            raise ValueError("wheat input overflow")
        self.wheat_in += n

    def take_wheat_in(self, amount: int) -> None:
        n = int(amount)
        if n < 0:
            raise ValueError("amount must be non-negative")
        if n > self.wheat_in:
            raise ValueError("insufficient wheat input")
        self.wheat_in -= n

    def water_amount(self) -> int:
        return int(self.water_in)

    def water_capacity(self) -> int:
        return self.storage_capacity()

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

    def beef_amount(self) -> int:
        return int(self.beef_out)

    def beef_capacity(self) -> int:
        return self.storage_capacity()

    def add_beef_out(self, amount: int) -> None:
        n = int(amount)
        if n < 0:
            raise ValueError("amount must be non-negative")
        if self.beef_out + n > self.beef_capacity():
            raise ValueError("beef output overflow")
        self.beef_out += n

    def take_beef_out(self, amount: int) -> None:
        n = int(amount)
        if n < 0:
            raise ValueError("amount must be non-negative")
        if n > self.beef_out:
            raise ValueError("insufficient beef output")
        self.beef_out -= n

    def hide_amount(self) -> int:
        return int(self.hide_out)

    def hide_capacity(self) -> int:
        return self.storage_capacity()

    def add_hide_out(self, amount: int) -> None:
        n = int(amount)
        if n < 0:
            raise ValueError("amount must be non-negative")
        if self.hide_out + n > self.hide_capacity():
            raise ValueError("hide output overflow")
        self.hide_out += n

    def take_hide_out(self, amount: int) -> None:
        n = int(amount)
        if n < 0:
            raise ValueError("amount must be non-negative")
        if n > self.hide_out:
            raise ValueError("insufficient hide output")
        self.hide_out -= n

    def processing_progress(self, now_ms: int) -> float:
        if self.processing_started_ms <= 0:
            return 0.0
        duration = max(1, int(self.processing_duration_ms))
        elapsed = max(0, int(now_ms) - int(self.processing_started_ms))
        return max(0.0, min(1.0, elapsed / float(duration)))

    def progress_state(self, now_ms: int) -> str:
        if self.processing_started_ms > 0 and self.processing_progress(now_ms) < 1.0:
            return "processing"
        return "idle"
