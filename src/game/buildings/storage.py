"""Shared storage behavior for resource-producing buildings."""

from __future__ import annotations

from game.config import building_level_int_setting


class StorageMixin:
    """Adds bounded integer storage API based on building level."""

    __slots__ = ()

    stored: int
    level: int

    def storage_capacity(self) -> int:
        return building_level_int_setting(self.type_tag, "storage", self.level)

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
