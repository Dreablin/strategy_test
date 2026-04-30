"""Sawmill building scaffold for Phase 20."""

from __future__ import annotations

from typing import ClassVar

from game.buildings.base import Building
from game.buildings.storage import BUILDING_STORAGE_BASE, BUILDING_STORAGE_PER_LEVEL


class Sawmill(Building):
    type_tag: ClassVar[str] = "SAWMILL"
    __slots__ = ("active", "wood_in", "boards_out", "processing_started_ms", "processing_duration_ms")

    def __init__(self, level: int = 1, grid_pos: tuple[int, int] | None = None) -> None:
        super().__init__(level=level, grid_pos=grid_pos)
        self.active = True
        self.wood_in = 0
        self.boards_out = 0
        self.processing_started_ms = 0
        self.processing_duration_ms = 30_000

    def set_active(self, value: bool) -> None:
        self.active = bool(value)

    def input_capacity(self) -> int:
        return BUILDING_STORAGE_BASE + BUILDING_STORAGE_PER_LEVEL * (self.level - 1)

    def output_capacity(self) -> int:
        return BUILDING_STORAGE_BASE + BUILDING_STORAGE_PER_LEVEL * (self.level - 1)

    def input_amount(self) -> int:
        return int(self.wood_in)

    def output_amount(self) -> int:
        return int(self.boards_out)

    def add_wood_in(self, amount: int) -> None:
        n = int(amount)
        if n < 0:
            raise ValueError("amount must be non-negative")
        if self.wood_in + n > self.input_capacity():
            raise ValueError("wood input overflow")
        self.wood_in += n

    def take_wood_in(self, amount: int) -> None:
        n = int(amount)
        if n < 0:
            raise ValueError("amount must be non-negative")
        if n > self.wood_in:
            raise ValueError("insufficient wood input")
        self.wood_in -= n

    def add_boards_out(self, amount: int) -> None:
        n = int(amount)
        if n < 0:
            raise ValueError("amount must be non-negative")
        if self.boards_out + n > self.output_capacity():
            raise ValueError("boards output overflow")
        self.boards_out += n

    def take_boards_out(self, amount: int) -> None:
        n = int(amount)
        if n < 0:
            raise ValueError("amount must be non-negative")
        if n > self.boards_out:
            raise ValueError("insufficient boards output")
        self.boards_out -= n

    def processing_progress(self, now_ms: int) -> float:
        if self.processing_started_ms <= 0:
            return 0.0
        duration = max(1, int(self.processing_duration_ms))
        elapsed = max(0, int(now_ms) - int(self.processing_started_ms))
        return max(0.0, min(1.0, elapsed / float(duration)))

    def progress_state(self, now_ms: int) -> str:
        return "processing" if self.processing_started_ms > 0 and self.processing_progress(now_ms) < 1.0 else "idle"
