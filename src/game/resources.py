"""Player resource balances (food, wood, stone, iron)."""

from collections.abc import Mapping
from typing import Final

from game.config import INITIAL_RESOURCES

_RESOURCE_NAMES: Final[tuple[str, ...]] = ("food", "wood", "stone", "iron")


class ResourceManager:
    """Tracks four resources with spend helpers and UI-facing per-cycle income."""

    __slots__ = ("_amounts", "_per_cycle")

    def __init__(self) -> None:
        self._amounts: dict[str, int] = dict(INITIAL_RESOURCES)
        self._per_cycle: dict[str, int] = {k: 0 for k in _RESOURCE_NAMES}

    def get(self, name: str) -> int:
        return self._amounts.get(name, 0)

    def add(self, name: str, amount: int) -> None:
        self._amounts[name] = max(0, self._amounts.get(name, 0) + amount)

    def has(self, cost: Mapping[str, int]) -> bool:
        return all(self.get(k) >= v for k, v in cost.items())

    def try_spend(self, cost: Mapping[str, int]) -> bool:
        if not self.has(cost):
            return False
        for k, v in cost.items():
            self._amounts[k] = self._amounts.get(k, 0) - v
        return True

    def set_per_cycle_totals(self, totals: Mapping[str, int]) -> None:
        """Replace per-cycle UI totals (from staffed production; PRD F-RES-04 / F-PROD)."""
        self._per_cycle = {k: max(0, int(totals.get(k, 0))) for k in _RESOURCE_NAMES}

    @property
    def per_cycle(self) -> dict[str, int]:
        return dict(self._per_cycle)
