"""Canteen building: local meal inputs, meal storage, and diner capacity."""

from __future__ import annotations

from typing import ClassVar

from game.buildings.base import Building

CANTEEN_LOCAL_RESOURCES: tuple[str, ...] = ("chicken", "bread", "water", "simple_meal")
CANTEEN_STORAGE_BASE = 5
CANTEEN_DINER_SLOTS_BASE = 3


class Canteen(Building):
    type_tag: ClassVar[str] = "CANTEEN"

    __slots__ = ("active", "_local_storage")

    def __init__(self, level: int = 1, grid_pos: tuple[int, int] | None = None) -> None:
        super().__init__(level=level, grid_pos=grid_pos)
        self.active = True
        self._local_storage = {resource: 0 for resource in CANTEEN_LOCAL_RESOURCES}

    def set_active(self, value: bool) -> None:
        self.active = bool(value)

    def local_storage_resources(self) -> tuple[str, ...]:
        return CANTEEN_LOCAL_RESOURCES

    def local_storage_capacity(self, resource: str) -> int:
        self._require_local_resource(resource)
        return CANTEEN_STORAGE_BASE + self.level - 1

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
        return CANTEEN_DINER_SLOTS_BASE + self.level - 1

    def _require_local_resource(self, resource: str) -> None:
        if resource not in self._local_storage:
            raise KeyError(resource)
