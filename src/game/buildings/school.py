"""School building with per-building worker training queue."""

from __future__ import annotations

from typing import ClassVar

from game.buildings.base import Building

SCHOOL_QUEUE_CAPACITY = 7
SCHOOL_TRAINING_MS = 30_000


class TrainingEntry:
    __slots__ = ("type_tag",)

    def __init__(self, type_tag: str) -> None:
        self.type_tag = type_tag


class School(Building):
    type_tag: ClassVar[str] = "SCHOOL"
    footprint: ClassVar[tuple[int, int]] = (2, 2)
    __slots__ = ("_queue", "_front_started_ms", "_progress_ms")

    def __init__(self, level: int = 1, grid_pos: tuple[int, int] | None = None) -> None:
        super().__init__(level=level, grid_pos=grid_pos)
        self._queue: list[TrainingEntry] = []
        self._front_started_ms: int | None = None
        self._progress_ms = 0

    def can_enqueue_training(self) -> bool:
        return len(self._queue) < SCHOOL_QUEUE_CAPACITY

    def enqueue_training(self, worker_type: str) -> bool:
        if not self.can_enqueue_training():
            return False
        self._queue.append(TrainingEntry(worker_type))
        if len(self._queue) == 1:
            self._front_started_ms = 0
            self._progress_ms = 0
        return True

    def training_queue(self) -> tuple[TrainingEntry, ...]:
        return tuple(self._queue)

    def training_progress_ms(self) -> int:
        return self._progress_ms

    def update_training(self, now_ms: int) -> str | None:
        if not self._queue:
            self._front_started_ms = None
            self._progress_ms = 0
            return None
        if self._front_started_ms is None:
            self._front_started_ms = int(now_ms)
        elapsed = max(0, int(now_ms) - self._front_started_ms)
        if elapsed < SCHOOL_TRAINING_MS:
            self._progress_ms = elapsed
            return None
        completed = self._queue.pop(0).type_tag
        if self._queue:
            self._front_started_ms = int(now_ms)
            self._progress_ms = 0
        else:
            self._front_started_ms = None
            self._progress_ms = 0
        return completed

    @classmethod
    def max_level(cls) -> int:
        return 1
