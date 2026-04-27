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
    alive: bool = True

    @property
    def stage_index(self) -> int:
        return int(self.stage)

    def cut_down(self) -> None:
        self.alive = False

    def remove(self) -> None:
        self.cut_down()


def stage_from_tile_seed(seed: int) -> TreeStage:
    """Pick a deterministic growth stage from any integer tile seed."""
    return TreeStage(seed % len(TreeStage))

