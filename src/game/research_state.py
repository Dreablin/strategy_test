"""In-memory research progress for the current run."""

from __future__ import annotations

from game.research_config import RESEARCH_BY_ID


class ResearchState:
    """Tracks completed researches and the single active research run."""

    __slots__ = ("_completed", "_active_id", "_delivered", "_points")

    def __init__(self) -> None:
        self._completed: set[str] = set()
        self._active_id: str | None = None
        self._delivered: dict[str, int] = {}
        self._points = 0

    def completed_ids(self) -> frozenset[str]:
        return frozenset(self._completed)

    def active_research_id(self) -> str | None:
        return self._active_id

    def delivered_amounts(self) -> dict[str, int]:
        return dict(self._delivered)

    def accumulated_points(self) -> int:
        return self._points

    def is_completed(self, research_id: str) -> bool:
        return str(research_id) in self._completed

    def has_active_research(self) -> bool:
        return self._active_id is not None

    def start_research(self, research_id: str) -> None:
        """Select *research_id* as the only active research."""
        key = str(research_id)
        if key not in RESEARCH_BY_ID:
            raise ValueError(f"unknown research id {key!r}")
        if key in self._completed:
            raise ValueError(f"research {key!r} is already completed")
        if self._active_id is not None:
            raise ValueError("another research is already active")
        definition = RESEARCH_BY_ID[key]
        self._active_id = key
        self._delivered = {resource: 0 for resource in definition.resource_cost}
        self._points = 0

    def mark_research_completed(self, research_id: str) -> None:
        """Mark *research_id* complete and clear its active progress."""
        key = str(research_id)
        if key not in RESEARCH_BY_ID:
            raise ValueError(f"unknown research id {key!r}")
        if key in self._completed:
            raise ValueError(f"research {key!r} is already completed")
        if self._active_id != key:
            raise ValueError(f"research {key!r} is not the active research")
        self._completed.add(key)
        self._active_id = None
        self._delivered.clear()
        self._points = 0

    def add_delivered(self, resource: str, amount: int) -> None:
        """Record delivered units for the active research input storage."""
        if self._active_id is None:
            raise ValueError("no active research")
        if amount <= 0:
            raise ValueError("amount must be positive")
        resource_key = str(resource)
        definition = RESEARCH_BY_ID[self._active_id]
        if resource_key not in definition.resource_cost:
            raise ValueError(f"resource {resource_key!r} is not required for active research")
        capacity = definition.resource_cost[resource_key]
        current = self._delivered.get(resource_key, 0)
        if current >= capacity:
            raise ValueError(f"resource {resource_key!r} is already fully delivered")
        self._delivered[resource_key] = min(current + amount, capacity)

    def add_points(self, amount: int) -> None:
        """Accumulate research points for the active research."""
        if self._active_id is None:
            raise ValueError("no active research")
        if amount < 0:
            raise ValueError("amount must be non-negative")
        self._points += amount

    def all_resources_delivered(self) -> bool:
        if self._active_id is None:
            return False
        definition = RESEARCH_BY_ID[self._active_id]
        return all(
            self._delivered.get(resource, 0) >= required
            for resource, required in definition.resource_cost.items()
        )
