"""Field building type used for wheat growth cycles."""

from __future__ import annotations

from typing import ClassVar

from game.buildings.base import Building

WHEAT_EMPTY = "EMPTY"
WHEAT_PHASE_1 = "PHASE_1"
WHEAT_PHASE_2 = "PHASE_2"
WHEAT_PHASE_3 = "PHASE_3"
WHEAT_PHASE_4 = "PHASE_4"
WHEAT_GROWTH_STEP_MS = 45_000

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


def on_field_harvest(current_phase: str) -> str:
    """Apply harvest action to a field phase and return resulting phase."""
    return reset_after_harvest(current_phase)


def is_ready_for_sowing(current_phase: str) -> bool:
    """Whether the field can be selected for sowing in current cycle."""
    return str(current_phase).upper() == WHEAT_EMPTY


def advance_wheat_growth(
    current_phase: str,
    last_change_ms: int,
    *,
    now_ms: int,
    growth_step_ms: int = WHEAT_GROWTH_STEP_MS,
) -> tuple[str, int]:
    phase = str(current_phase).upper()
    if phase not in _WHEAT_PHASE_ORDER:
        raise ValueError(f"unknown wheat phase: {current_phase!r}")
    if phase in {WHEAT_EMPTY, WHEAT_PHASE_4}:
        return phase, int(last_change_ms)

    if int(now_ms) - int(last_change_ms) < int(growth_step_ms):
        return phase, int(last_change_ms)

    updated_at = int(last_change_ms)
    while phase not in {WHEAT_EMPTY, WHEAT_PHASE_4} and int(now_ms) - updated_at >= int(growth_step_ms):
        phase = next_wheat_phase(phase)
        updated_at += int(growth_step_ms)
    return phase, updated_at


class Field(Building):
    type_tag: ClassVar[str] = "FIELD"
    footprint: ClassVar[tuple[int, int]] = (1, 1)
    __slots__ = ("wheat_phase", "wheat_last_change_ms")

    def __init__(self, level: int = 1, grid_pos: tuple[int, int] | None = None) -> None:
        super().__init__(level=level, grid_pos=grid_pos)
        self.wheat_phase = WHEAT_EMPTY
        self.wheat_last_change_ms = 0

    @classmethod
    def max_level(cls) -> int:
        return 1

    def set_wheat_phase(self, phase: str, *, now_ms: int | None = None) -> None:
        normalized = str(phase).upper()
        if normalized not in _WHEAT_PHASE_ORDER:
            raise ValueError(f"unknown wheat phase: {phase!r}")
        self.wheat_phase = normalized
        if now_ms is not None:
            self.wheat_last_change_ms = int(now_ms)

    def sow(self, *, now_ms: int) -> None:
        self.set_wheat_phase(WHEAT_PHASE_1, now_ms=now_ms)

    def harvest(self, *, now_ms: int) -> None:
        self.set_wheat_phase(reset_after_harvest(self.wheat_phase), now_ms=now_ms)

    def update_wheat_growth(self, now_ms: int) -> None:
        phase, changed_at = advance_wheat_growth(
            self.wheat_phase,
            self.wheat_last_change_ms,
            now_ms=int(now_ms),
        )
        self.wheat_phase = phase
        self.wheat_last_change_ms = changed_at
