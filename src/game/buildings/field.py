"""Field building type used for wheat growth cycles."""

from __future__ import annotations

from typing import ClassVar

from game.buildings.base import Building

WHEAT_EMPTY = "EMPTY"
WHEAT_PHASE_1 = "PHASE_1"
WHEAT_PHASE_2 = "PHASE_2"
WHEAT_PHASE_3 = "PHASE_3"
WHEAT_PHASE_4 = "PHASE_4"

_WHEAT_PHASE_ORDER: tuple[str, ...] = (
    WHEAT_EMPTY,
    WHEAT_PHASE_1,
    WHEAT_PHASE_2,
    WHEAT_PHASE_3,
    WHEAT_PHASE_4,
)


def next_wheat_phase(current_phase: str) -> str:
    phase = str(current_phase).upper()
    if phase == WHEAT_EMPTY:
        return WHEAT_PHASE_1
    if phase == WHEAT_PHASE_1:
        return WHEAT_PHASE_2
    if phase == WHEAT_PHASE_2:
        return WHEAT_PHASE_3
    if phase == WHEAT_PHASE_3:
        return WHEAT_PHASE_4
    if phase == WHEAT_PHASE_4:
        return WHEAT_PHASE_4
    raise ValueError(f"unknown wheat phase: {current_phase!r}")


def reset_after_harvest(current_phase: str) -> str:
    phase = str(current_phase).upper()
    if phase != WHEAT_PHASE_4:
        raise ValueError("harvest reset requires PHASE_4")
    return WHEAT_EMPTY


class Field(Building):
    type_tag: ClassVar[str] = "FIELD"
    footprint: ClassVar[tuple[int, int]] = (1, 1)

    @classmethod
    def max_level(cls) -> int:
        return 1
