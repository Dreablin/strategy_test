"""Construction domain model and helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class ConstructionSite:
    required_resources: dict[str, int]
    delivered_resources: dict[str, int]
    build_time_ms: int
    build_started_ms: int | None
    builder: Any | None
    target_level: int

    def is_fully_supplied(self) -> bool:
        for key, required in self.required_resources.items():
            if int(self.delivered_resources.get(key, 0)) < int(required):
                return False
        return True

    def is_building(self) -> bool:
        return self.is_fully_supplied() and self.build_started_ms is not None

    def build_progress(self, now_ms: int) -> float:
        if not self.is_building():
            return 0.0
        assert self.build_started_ms is not None
        elapsed = max(0, int(now_ms) - int(self.build_started_ms))
        duration = max(1, int(self.build_time_ms))
        return max(0.0, min(1.0, elapsed / float(duration)))

    def is_complete(self, now_ms: int) -> bool:
        return self.build_progress(now_ms) >= 1.0

    def remaining_resources(self) -> dict[str, int]:
        remaining: dict[str, int] = {}
        for key, required in self.required_resources.items():
            delivered = int(self.delivered_resources.get(key, 0))
            remaining[key] = max(0, int(required) - delivered)
        return remaining

    def deliver_resource(self, resource: str, amount: int) -> None:
        n = int(amount)
        if n < 0:
            raise ValueError("amount must be non-negative")
        key = str(resource).lower()
        required = int(self.required_resources.get(key, 0))
        current = int(self.delivered_resources.get(key, 0))
        if required <= 0:
            self.delivered_resources[key] = 0
            return
        self.delivered_resources[key] = min(required, current + n)
