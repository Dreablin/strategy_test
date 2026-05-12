"""Canteen building: local meal inputs, meal storage, and diner capacity."""

from __future__ import annotations

from typing import ClassVar

from game.buildings.base import Building
from game.config import building_level_int_setting
from game.worker_constants import CANTEEN_CYCLE_MS
from game.worker_models import Worker

CANTEEN_LOCAL_RESOURCES: tuple[str, ...] = ("chicken", "bread", "water", "simple_meal")
CANTEEN_STORAGE_BASE = building_level_int_setting("CANTEEN", "storage", 1)
CANTEEN_DINER_SLOTS_BASE = building_level_int_setting("CANTEEN", "diner_slots", 1)


class Canteen(Building):
    type_tag: ClassVar[str] = "CANTEEN"

    __slots__ = (
        "active",
        "_local_storage",
        "_diner_occupants",
        "_reserved_meal_workers",
        "_diner_queue_seq",
        "processing_started_ms",
        "processing_duration_ms",
    )

    def __init__(self, level: int = 1, grid_pos: tuple[int, int] | None = None) -> None:
        super().__init__(level=level, grid_pos=grid_pos)
        self.active = True
        self._local_storage = {resource: 0 for resource in CANTEEN_LOCAL_RESOURCES}
        self._diner_occupants: set[Worker] = set()
        self._reserved_meal_workers: set[Worker] = set()
        self._diner_queue_seq = 0
        self.processing_started_ms = 0
        self.processing_duration_ms = CANTEEN_CYCLE_MS

    def set_active(self, value: bool) -> None:
        self.active = bool(value)

    def local_storage_resources(self) -> tuple[str, ...]:
        return CANTEEN_LOCAL_RESOURCES

    def local_storage_capacity(self, resource: str) -> int:
        self._require_local_resource(resource)
        return building_level_int_setting(self.type_tag, "storage", self.level)

    def local_storage_amount(self, resource: str) -> int:
        self._require_local_resource(resource)
        return int(self._local_storage[resource])

    def add_local_storage(self, resource: str, amount: int) -> None:
        self._require_local_resource(resource)
        n = int(amount)
        if n < 0:
            raise ValueError("amount must be non-negative")
        if self._local_storage[resource] + n > self.local_storage_capacity(resource):
            raise ValueError(f"{resource} local storage overflow")
        self._local_storage[resource] += n

    def take_local_storage(self, resource: str, amount: int) -> None:
        self._require_local_resource(resource)
        n = int(amount)
        if n < 0:
            raise ValueError("amount must be non-negative")
        if n > self._local_storage[resource]:
            raise ValueError(f"insufficient {resource} local storage")
        self._local_storage[resource] -= n

    def diner_slot_capacity(self) -> int:
        return building_level_int_setting(self.type_tag, "diner_slots", self.level)

    def has_recipe_inputs(self) -> bool:
        return (
            self.local_storage_amount("chicken") >= 1
            and self.local_storage_amount("bread") >= 1
            and self.local_storage_amount("water") >= 1
        )

    def output_amount(self) -> int:
        return self.local_storage_amount("simple_meal")

    def output_capacity(self) -> int:
        return self.local_storage_capacity("simple_meal")

    def processing_progress(self, now_ms: int) -> float:
        if self.processing_started_ms <= 0:
            return 0.0
        duration = max(1, int(self.processing_duration_ms))
        elapsed = max(0, int(now_ms) - int(self.processing_started_ms))
        return max(0.0, min(1.0, elapsed / float(duration)))

    def progress_state(self, now_ms: int) -> str:
        return (
            "processing"
            if self.processing_started_ms > 0 and self.processing_progress(now_ms) < 1.0
            else "idle"
        )

    def meal_resource_key(self) -> str:
        return "simple_meal"

    def dining_tier(self) -> str:
        return "basic"

    def water_amount(self) -> int:
        return self.local_storage_amount("water")

    def water_capacity(self) -> int:
        return self.local_storage_capacity("water")

    def add_water_in(self, amount: int) -> None:
        self.add_local_storage("water", int(amount))

    def _require_local_resource(self, resource: str) -> None:
        if resource not in self._local_storage:
            raise KeyError(resource)
