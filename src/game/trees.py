"""Tree domain models and deterministic stage selection."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum


class TreeStage(IntEnum):
    """Ordered growth stages for tree entities."""

    SAPLING = 0
    YOUNG = 1
    MATURE = 2
    ADULT = 3


@dataclass(slots=True)
class Tree:
    """Single tree entity with growth stage and alive/removed state."""

    stage: TreeStage
    species: int = 0
    alive: bool = True
    next_growth_at_ms: int | None = None

    def __post_init__(self) -> None:
        if self.species not in (0, 1, 2):
            raise ValueError("tree species must be one of: 0, 1, 2")

    @property
    def stage_index(self) -> int:
        return int(self.stage)

    @property
    def can_chop(self) -> bool:
        return self.stage == TreeStage.ADULT and self.alive

    def update_growth(self, now_ms: int, *, growth_step_ms: int = 30_000) -> None:
        """Advance growth in fixed-size ticks, capped at ADULT stage."""
        if self.next_growth_at_ms is None:
            return
        while now_ms >= self.next_growth_at_ms:
            if self.stage < TreeStage.ADULT:
                self.stage = TreeStage(self.stage + 1)
            self.next_growth_at_ms += growth_step_ms

    def cut_down(self) -> None:
        self.alive = False

    def remove(self) -> None:
        self.cut_down()


def stage_from_tile_seed(seed: int) -> TreeStage:
    """Pick a deterministic growth stage from any integer tile seed."""
    return TreeStage(seed % len(TreeStage))

