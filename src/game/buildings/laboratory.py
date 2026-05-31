"""Laboratory building shell for scientist staffing and research runtime."""

from __future__ import annotations

from typing import ClassVar

from game.buildings.base import Building
from game.config import building_int_setting, building_level_int_setting, building_setting

_MIN_TECH_TIER = 1
_MAX_TECH_TIER = 4


class Laboratory(Building):
    type_tag: ClassVar[str] = "LABORATORY"
    footprint: ClassVar[tuple[int, int]] = (2, 2)
    __slots__ = ("active", "_research_input_capacities", "_research_input_delivered")

    def __init__(self, level: int = 1, grid_pos: tuple[int, int] | None = None) -> None:
        super().__init__(level=level, grid_pos=grid_pos)
        self.active = True
        self._research_input_capacities: dict[str, int] = {}
        self._research_input_delivered: dict[str, int] = {}

    @classmethod
    def max_level(cls) -> int:
        return 10

    def set_active(self, value: bool) -> None:
        self.active = bool(value)

    def scientist_slot_capacity(self) -> int:
        return building_level_int_setting(self.type_tag, "scientist_slots", self.level)

    def research_points_per_scientist_per_second(self) -> int:
        return building_int_setting(self.type_tag, "research", "points_per_scientist_per_second")

    def technology_tier_unlock_level(self, tier: int) -> int:
        tier_num = int(tier)
        if tier_num < _MIN_TECH_TIER or tier_num > _MAX_TECH_TIER:
            raise ValueError(
                f"technology tier must be in [{_MIN_TECH_TIER}, {_MAX_TECH_TIER}], got {tier_num}"
            )
        unlock = building_setting(self.type_tag, "technology_tiers", "unlock_level_by_tier")
        if not isinstance(unlock, dict):
            raise ValueError("technology_tiers.unlock_level_by_tier must be an object")
        key = str(tier_num)
        if key not in unlock:
            raise KeyError(f"missing unlock level for technology tier {tier_num}")
        return int(unlock[key])

    def unlocks_technology_tier(self, tier: int) -> bool:
        return self.level >= self.technology_tier_unlock_level(tier)

    def clear_research_input_storage(self) -> None:
        self._research_input_capacities.clear()
        self._research_input_delivered.clear()

    def initialize_research_input_storage(self, resource_cost: dict[str, int]) -> None:
        """Prepare empty local input slots for an active research cost map."""
        self.clear_research_input_storage()
        for resource, amount in resource_cost.items():
            key = str(resource)
            capacity = int(amount)
            if capacity <= 0:
                raise ValueError(f"resource_cost[{key!r}] must be positive")
            self._research_input_capacities[key] = capacity
            self._research_input_delivered[key] = 0

    def has_research_input_storage(self) -> bool:
        return bool(self._research_input_capacities)

    def research_input_resources(self) -> tuple[str, ...]:
        return tuple(self._research_input_capacities)

    def research_input_capacity(self, resource: str) -> int:
        return int(self._research_input_capacities.get(str(resource), 0))

    def research_input_amount(self, resource: str) -> int:
        return int(self._research_input_delivered.get(str(resource), 0))

    def research_input_amounts(self) -> dict[str, int]:
        return dict(self._research_input_delivered)

    def all_research_inputs_delivered(self) -> bool:
        if not self._research_input_capacities:
            return False
        return all(
            self._research_input_delivered.get(resource, 0) >= capacity
            for resource, capacity in self._research_input_capacities.items()
        )

    def accepts_research_input(self, resource: str) -> bool:
        return str(resource) in self._research_input_capacities

    def add_research_input(self, resource: str, amount: int = 1) -> None:
        """Deliver units into active research local input storage."""
        key = str(resource)
        if key not in self._research_input_capacities:
            raise ValueError(f"resource {key!r} is not required for active research")
        if amount <= 0:
            raise ValueError("amount must be positive")
        capacity = self._research_input_capacities[key]
        current = self._research_input_delivered.get(key, 0)
        if current >= capacity:
            raise ValueError(f"resource {key!r} is already fully delivered")
        self._research_input_delivered[key] = min(current + int(amount), capacity)
