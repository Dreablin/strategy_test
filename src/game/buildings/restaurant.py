"""Restaurant building: advanced dining with elite_meal for advanced-tier workers."""

from __future__ import annotations

from typing import ClassVar

from game.buildings.base import Building
from game.config import building_level_int_setting, building_setting
from game.worker_models import Worker

RESTAURANT_LOCAL_RESOURCES: tuple[str, ...] = ("bread", "wine", "beef", "elite_meal")


class Restaurant(Building):
    type_tag: ClassVar[str] = "RESTAURANT"

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
        self._local_storage = {resource: 0 for resource in RESTAURANT_LOCAL_RESOURCES}
        self._diner_occupants: set[Worker] = set()
        self._reserved_meal_workers: set[Worker] = set()
        self._diner_queue_seq = 0
        self.processing_started_ms = 0
        self.processing_duration_ms = 0

    def set_active(self, value: bool) -> None:
        self.active = bool(value)

    def local_storage_resources(self) -> tuple[str, ...]:
        return RESTAURANT_LOCAL_RESOURCES

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

    def meal_resource_key(self) -> str:
        return str(building_setting(self.type_tag, "dining", "meal_resource"))

    def dining_tier(self) -> str:
        return str(building_setting(self.type_tag, "dining", "tier"))

    def recipe_input(self) -> dict[str, int]:
        raw = building_setting(self.type_tag, "recipe", "input")
        return {str(k): int(v) for k, v in raw.items()}

    def recipe_output(self) -> dict[str, int]:
        raw = building_setting(self.type_tag, "recipe", "output")
        return {str(k): int(v) for k, v in raw.items()}

    def recipe_input_count(self) -> dict[str, int]:
        return self.recipe_input()

    def recipe_output_count(self) -> int:
        out = self.recipe_output()
        return sum(out.values())

    def has_recipe_inputs(self) -> bool:
        for resource, needed in self.recipe_input().items():
            if self.local_storage_amount(resource) < needed:
                return False
        return True

    def output_amount(self) -> int:
        return self.local_storage_amount(self.meal_resource_key())

    def output_capacity(self) -> int:
        return self.local_storage_capacity(self.meal_resource_key())

    def input_amount(self, resource: str | None = None) -> int:
        if resource is not None:
            return self.local_storage_amount(resource)
        return sum(self._local_storage[r] for r in self.recipe_input())

    def input_capacity(self, resource: str | None = None) -> int:
        if resource is not None:
            return self.local_storage_capacity(resource)
        return sum(self.local_storage_capacity(r) for r in self.recipe_input())

    def cycle_ms(self) -> int:
        return int(building_setting(self.type_tag, "production", "cycle_ms"))

    def rest_ms(self) -> int:
        return int(building_setting(self.type_tag, "production", "rest_ms"))

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

    def _require_local_resource(self, resource: str) -> None:
        if resource not in self._local_storage:
            raise KeyError(resource)
