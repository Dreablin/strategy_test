"""Research gates for mission statue construction stages."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from game.research_state import ResearchState

STATUE_STAGE_RESEARCH_BY_LEVEL: dict[int, str] = {
    1: "statue_excavation",
    2: "statue_foundation",
    3: "statue_pedestal",
    4: "statue_monument",
}


def statue_stage_research_id(target_level: int) -> str | None:
    return STATUE_STAGE_RESEARCH_BY_LEVEL.get(int(target_level))


def statue_stage_unlocked(research_state: ResearchState | None, target_level: int) -> bool:
    research_id = statue_stage_research_id(target_level)
    if research_id is None:
        return True
    if research_state is None:
        return True
    return research_state.is_completed(research_id)
