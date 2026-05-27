"""Complete active research when accumulated points reach the requirement."""

from __future__ import annotations

from game.buildings.laboratory import Laboratory
from game.research_config import RESEARCH_BY_ID
from game.research_state import ResearchState


def active_research_required_points(research_state: ResearchState) -> int | None:
    """Configured point requirement for the active research, if any."""
    active_id = research_state.active_research_id()
    if active_id is None:
        return None
    return RESEARCH_BY_ID[active_id].required_points


def try_complete_active_research(
    *,
    research_state: ResearchState,
    laboratory: Laboratory | None = None,
) -> bool:
    """Mark the active research complete when its point requirement is met."""
    active_id = research_state.active_research_id()
    if active_id is None:
        return False
    required = RESEARCH_BY_ID[active_id].required_points
    if research_state.accumulated_points() < required:
        return False
    research_state.mark_research_completed(active_id)
    if laboratory is not None:
        laboratory.clear_research_input_storage()
    return True
