"""Chicken farm building: processes wheat and water into chicken."""

from __future__ import annotations

from typing import ClassVar

from game.buildings.base import Building
from game.config import building_int_setting, building_level_int_setting, building_setting


class ChickenFarm(Building):
    type_tag: ClassVar[str] = "CHICKEN_FARM"
    __slots__ = (
        "active",
        "wheat_in",
        "water_in",
        "chicken_out",
        "processing_started_ms",
        "processing_duration_ms",
    )

    def __init__(self, level: int = 1, grid_pos: tuple[int, int] | None = None) -> None:
        super().__init__(level=level, grid_pos=grid_pos)
        self.active = True
        self.wheat_in = 0
        self.water_in = 0
        self.chicken_out = 0
        self.processing_started_ms = 0
        self.processing_duration_ms = self.cycle_ms()

    def set_active(self, value: bool) -> None:
        self.active = bool(value)

    def storage_capacity(self) -> int:
        return building_level_int_setting(self.type_tag, "storage", self.level)

    def input_capacity(self) -> int:
        return self.storage_capacity()

    def water_capacity(self) -> int:
        return self.storage_capacity()

    def output_capacity(self) -> int:
        return self.storage_capacity()

    def input_amount(self) -> int:
        return int(self.wheat_in)

    def water_amount(self) -> int:
        return int(self.water_in)

    def output_amount(self) -> int:
        return int(self.chicken_out)

    def recipe_input(self) -> dict[str, int]:
        raw = building_setting(self.type_tag, "recipe", "input")
        return {str(k): int(v) for k, v in raw.items()}

    def recipe_output(self) -> dict[str, int]:
        raw = building_setting(self.type_tag, "recipe", "output")
        return {str(k): int(v) for k, v in raw.items()}

    def cycle_ms(self) -> int:
        return building_int_setting(self.type_tag, "production", "cycle_ms")

    def rest_ms(self) -> int:
        return building_int_setting(self.type_tag, "production", "rest_ms")

    def has_recipe_inputs(self) -> bool:
        return all(self._resource_amount(resource) >= needed for resource, needed in self.recipe_input().items())

    def _resource_amount(self, resource: str) -> int:
        if resource == "wheat":
            return self.input_amount()
        if resource == "water":
            return self.water_amount()
        raise KeyError(resource)

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

    def add_chicken_out(self, amount: int) -> None:
        n = int(amount)
        if n < 0:
            raise ValueError("amount must be non-negative")
        if self.chicken_out + n > self.output_capacity():
            raise ValueError("chicken output overflow")
        self.chicken_out += n

    def take_chicken_out(self, amount: int) -> None:
        n = int(amount)
        if n < 0:
            raise ValueError("amount must be non-negative")
        if n > self.chicken_out:
            raise ValueError("insufficient chicken output")
        self.chicken_out -= n

    def processing_progress(self, now_ms: int) -> float:
        if self.processing_started_ms <= 0:
            return 0.0
        duration = max(1, int(self.processing_duration_ms))
        elapsed = max(0, int(now_ms) - int(self.processing_started_ms))
        return max(0.0, min(1.0, elapsed / float(duration)))

    def progress_state(self, now_ms: int) -> str:
        return "processing" if self.processing_started_ms > 0 and self.processing_progress(now_ms) < 1.0 else "idle"
