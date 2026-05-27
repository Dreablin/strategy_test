"""Research tile full-color vs dimmed visual state."""

from __future__ import annotations

from game.research_state import ResearchState

_DIMMED_ALPHA = 140
_FULL_ALPHA = 255
_DIMMED_TITLE_COLOR = (150, 156, 168)
_FULL_TITLE_COLOR = (232, 236, 244)


def research_tile_uses_full_color(research_id: str, research_state: ResearchState | None) -> bool:
    """Completed tiles are full-color; not-started and in-progress tiles are dimmed."""
    return research_state is not None and research_state.is_completed(research_id)


def research_tile_image_alpha(research_id: str, research_state: ResearchState | None) -> int:
    return _FULL_ALPHA if research_tile_uses_full_color(research_id, research_state) else _DIMMED_ALPHA


def research_tile_title_color(research_id: str, research_state: ResearchState | None) -> tuple[int, int, int]:
    return (
        _FULL_TITLE_COLOR
        if research_tile_uses_full_color(research_id, research_state)
        else _DIMMED_TITLE_COLOR
    )
