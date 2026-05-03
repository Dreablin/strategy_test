"""Gold world deposit domain model."""

from __future__ import annotations


class GoldDeposit:
    """World gold visual/resource marker.

    Blocking deposits form the central vein. Buildable deposits are passable
    ore fragments reserved for future gold mine placement.
    """

    __slots__ = ("blocking", "variant")

    def __init__(self, *, blocking: bool, variant: int = 0) -> None:
        self.blocking = bool(blocking)
        self.variant = int(variant)
        if self.variant < 0 or self.variant > 4:
            raise ValueError("variant must be in range [0, 4]")

    @property
    def buildable(self) -> bool:
        return not self.blocking
