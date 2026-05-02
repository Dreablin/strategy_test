"""Mill building: processes wheat into flour."""

from __future__ import annotations

from typing import ClassVar

from game.buildings.base import Building
from game.buildings.storage import BUILDING_STORAGE_BASE

MILL_STORAGE_BASE = BUILDING_STORAGE_BASE


class Mill(Building):
    type_tag: ClassVar[str] = "MILL"
    __slots__ = ("active", "wheat_in", "flour_out", "processing_started_ms", "processing_duration_ms")

    def __init__(self, level: int = 1, grid_pos: tuple[int, int] | None = None) -> None:
        super().__init__(level=level, grid_pos=grid_pos)
        self.active = True
        self.wheat_in = 0
        self.flour_out = 0
        self.processing_started_ms = 0
        self.processing_duration_ms = 30_000

    def set_active(self, value: bool) -> None:
        self.active = bool(value)

    def input_capacity(self) -> int:
        milestones = int(self.level >= 5) + int(self.level >= 10)
        return MILL_STORAGE_BASE + milestones

    def output_capacity(self) -> int:
        milestones = int(self.level >= 5) + int(self.level >= 10)
        return MILL_STORAGE_BASE + milestones

    def input_amount(self) -> int:
        return int(self.wheat_in)

    def output_amount(self) -> int:
        return int(self.flour_out)

    def add_wheat_in(self, amount: int) -> None:
        n = int(amount)
        if n < 0:
            raise ValueError("amount must be non-negative")
        if self.wheat_in + n > self.input_capacity():
            raise ValueError("wheat input overflow")
        self.wheat_in += n

    def take_wheat_in(self, amount: int) -> None:
        n = int(amount)
        if n < 0:
            raise ValueError("amount must be non-negative")
        if n > self.wheat_in:
            raise ValueError("insufficient wheat input")
        self.wheat_in -= n

    def add_flour_out(self, amount: int) -> None:
        n = int(amount)
        if n < 0:
            raise ValueError("amount must be non-negative")
        if self.flour_out + n > self.output_capacity():
            raise ValueError("flour output overflow")
        self.flour_out += n

    def take_flour_out(self, amount: int) -> None:
        n = int(amount)
        if n < 0:
            raise ValueError("amount must be non-negative")
        if n > self.flour_out:
            raise ValueError("insufficient flour output")
        self.flour_out -= n

    def processing_progress(self, now_ms: int) -> float:
        if self.processing_started_ms <= 0:
            return 0.0
        duration = max(1, int(self.processing_duration_ms))
        elapsed = max(0, int(now_ms) - int(self.processing_started_ms))
        return max(0.0, min(1.0, elapsed / float(duration)))

    def progress_state(self, now_ms: int) -> str:
        return "processing" if self.processing_started_ms > 0 and self.processing_progress(now_ms) < 1.0 else "idle"
