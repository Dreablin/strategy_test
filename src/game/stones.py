"""Stone resource domain model."""

from __future__ import annotations


class Stone:
    """Harvestable stone node with finite units."""

    __slots__ = ("units",)

    def __init__(self, units: int = 15) -> None:
        self.units = int(units)
        if self.units < 0:
            raise ValueError("units must be non-negative")

    @property
    def is_depleted(self) -> bool:
        return self.units == 0

    def harvest(self) -> int:
        if self.units <= 0:
            raise ValueError("stone is depleted")
        self.units -= 1
        return self.units
