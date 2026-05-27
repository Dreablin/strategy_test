"""Research tile completion visual state tests (T412)."""

from __future__ import annotations

import pygame

from game.research_state import ResearchState
from game.ui.research_screen_layout import compute_content_layout
from game.ui.research_tile_visual import (
    research_tile_image_alpha,
    research_tile_uses_full_color,
)
from game.ui.research_tiles import draw_research_tiles


def _tile_by_id(content, research_id: str):
    return next(t for t in content.tiles if t.research_id == research_id)


def test_completed_research_uses_full_color_flag() -> None:
    state = ResearchState()
    state.start_research("1")
    state.mark_research_completed("1")
    state.start_research("2")
    assert research_tile_uses_full_color("1", state) is True
    assert research_tile_uses_full_color("2", state) is False
    assert research_tile_uses_full_color("3", state) is False


def test_image_alpha_full_for_completed_dimmed_otherwise() -> None:
    state = ResearchState()
    state.start_research("1")
    state.mark_research_completed("1")
    assert research_tile_image_alpha("1", state) == 255
    assert research_tile_image_alpha("2", None) == 140
    state.start_research("2")
    assert research_tile_image_alpha("2", state) == 140


def test_draw_completed_tile_brighter_than_active_tile() -> None:
    surface = pygame.Surface((1280, 720))
    content = compute_content_layout(surface)
    state = ResearchState()
    state.start_research("1")
    state.mark_research_completed("1")
    state.start_research("2")
    draw_research_tiles(surface, content.tiles, research_state=state)
    completed = _tile_by_id(content, "1")
    active = _tile_by_id(content, "2")
    completed_px = surface.get_at(completed.image_rect.center)
    active_px = surface.get_at(active.image_rect.center)
    assert sum(completed_px[:3]) > sum(active_px[:3])


def test_draw_not_started_tile_is_dimmed() -> None:
    surface = pygame.Surface((1280, 720))
    content = compute_content_layout(surface)
    state = ResearchState()
    draw_research_tiles(surface, content.tiles, research_state=state)
    tile = _tile_by_id(content, "3")
    dimmed_px = surface.get_at(tile.image_rect.center)
    state.start_research("3")
    state.mark_research_completed("3")
    surface2 = pygame.Surface((1280, 720))
    content2 = compute_content_layout(surface2)
    draw_research_tiles(surface2, content2.tiles, research_state=state)
    full_px = surface2.get_at(_tile_by_id(content2, "3").image_rect.center)
    assert sum(full_px[:3]) > sum(dimmed_px[:3])
