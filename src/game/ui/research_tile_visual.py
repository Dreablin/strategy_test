"""Research tile full-color, in-progress, and dimmed visual state."""

from __future__ import annotations

from game.research_state import ResearchState

_DIMMED_ALPHA = 140
_IN_PROGRESS_ALPHA = 210
_FULL_ALPHA = 255
_DIMMED_TITLE_COLOR = (150, 156, 168)
_IN_PROGRESS_TITLE_COLOR = (140, 188, 232)
_FULL_TITLE_COLOR = (232, 236, 244)


def research_tile_is_in_progress(research_id: str, research_state: ResearchState | None) -> bool:
    if research_state is None:
        return False
    active_id = research_state.active_research_id()
    return active_id is not None and str(research_id) == active_id


def research_tile_uses_full_color(research_id: str, research_state: ResearchState | None) -> bool:
    """Completed tiles are full-color; not-started and in-progress tiles are not."""
    return research_state is not None and research_state.is_completed(research_id)


def research_tile_image_alpha(research_id: str, research_state: ResearchState | None) -> int:
    if research_tile_uses_full_color(research_id, research_state):
        return _FULL_ALPHA
    if research_tile_is_in_progress(research_id, research_state):
        return _IN_PROGRESS_ALPHA
    return _DIMMED_ALPHA


def research_tile_title_color(research_id: str, research_state: ResearchState | None) -> tuple[int, int, int]:
    if research_tile_uses_full_color(research_id, research_state):
        return _FULL_TITLE_COLOR
    if research_tile_is_in_progress(research_id, research_state):
        return _IN_PROGRESS_TITLE_COLOR
    return _DIMMED_TITLE_COLOR
