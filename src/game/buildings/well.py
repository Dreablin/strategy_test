"""Well building: water producer with local storage for carrier pickup."""

from __future__ import annotations

from typing import ClassVar

from game.buildings.base import Building
from game.buildings.storage import StorageMixin
from game.config import building_int_setting

WELL_LOCAL_RESOURCES: tuple[str, ...] = ("water",)
WELL_CYCLE_MS = building_int_setting("WELL", "production", "cycle_ms")
WELL_REST_MS = building_int_setting("WELL", "production", "rest_ms")


class Well(StorageMixin, Building):
    type_tag: ClassVar[str] = "WELL"
    footprint: ClassVar[tuple[int, int]] = (2, 2)
    __slots__ = ("active", "stored", "processing_started_ms", "processing_duration_ms", "rest_duration_ms")

    def __init__(self, level: int = 1, grid_pos: tuple[int, int] | None = None) -> None:
        super().__init__(level=level, grid_pos=grid_pos)
        self.active = True
        self.stored = 0
        self.processing_started_ms = 0
        self.processing_duration_ms = WELL_CYCLE_MS
        self.rest_duration_ms = WELL_REST_MS

    @classmethod
    def max_level(cls) -> int:
        return 10

    def set_active(self, value: bool) -> None:
        self.active = bool(value)

    def local_storage_resources(self) -> tuple[str, ...]:
        return WELL_LOCAL_RESOURCES

    def local_storage_capacity(self, resource: str) -> int:
        self._require_local_resource(resource)
        return self.storage_capacity()

    def local_storage_amount(self, resource: str) -> int:
        self._require_local_resource(resource)
        return int(self.stored)

    def add_local_storage(self, resource: str, amount: int) -> None:
        self._require_local_resource(resource)
        self.add_to_storage(amount)

    def take_local_storage(self, resource: str, amount: int) -> None:
        self._require_local_resource(resource)
        self.take_from_storage(amount)

    def output_amount(self) -> int:
        return self.local_storage_amount("water")

    def output_capacity(self) -> int:
        return self.local_storage_capacity("water")

    def water_amount(self) -> int:
        return self.local_storage_amount("water")

    def water_capacity(self) -> int:
        return self.local_storage_capacity("water")

    def add_water_in(self, amount: int) -> None:
        self.add_local_storage("water", amount)

    def take_water_in(self, amount: int) -> None:
        self.take_local_storage("water", amount)

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

    @staticmethod
    def _require_local_resource(resource: str) -> None:
        if resource != "water":
            raise KeyError(resource)
