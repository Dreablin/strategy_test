"""Shared storage behavior for resource-producing buildings."""

from __future__ import annotations

BUILDING_STORAGE_BASE = 3
BUILDING_STORAGE_PER_LEVEL = 2


class StorageMixin:
    """Adds bounded integer storage API based on building level."""

    __slots__ = ()

    stored: int
    level: int

    def storage_capacity(self) -> int:
        return BUILDING_STORAGE_BASE + BUILDING_STORAGE_PER_LEVEL * (self.level - 1)

    def add_to_storage(self, amount: int) -> None:
        n = int(amount)
        if n < 0:
            raise ValueError("amount must be non-negative")
        if self.stored + n > self.storage_capacity():
            raise ValueError("storage overflow")
        self.stored += n

    def take_from_storage(self, amount: int) -> None:
        n = int(amount)
        if n < 0:
            raise ValueError("amount must be non-negative")
        if n > self.stored:
            raise ValueError("insufficient stored amount")
        self.stored -= n

    def is_storage_full(self) -> bool:
        return self.stored == self.storage_capacity()
