"""Research screen in-progress tile visual state tests (T434)."""

from __future__ import annotations

import pygame

from game.research_state import ResearchState
from game.ui.research_screen_layout import compute_content_layout
from game.ui.research_tile_visual import (
    research_tile_image_alpha,
    research_tile_is_in_progress,
    research_tile_uses_full_color,
)
from game.ui.research_tiles import draw_research_tiles


def _tile_by_id(content, research_id: str):
    return next(t for t in content.tiles if t.research_id == research_id)


def test_in_progress_flag_and_alpha() -> None:
    state = ResearchState()
    assert not research_tile_is_in_progress("1", state)
    assert research_tile_image_alpha("1", state) == 140
    state.start_research("1")
    assert research_tile_is_in_progress("1", state)
    assert not research_tile_is_in_progress("2", state)
    assert research_tile_image_alpha("1", state) == 210
    assert research_tile_image_alpha("2", state) == 140
    assert not research_tile_uses_full_color("1", state)


def test_completed_and_not_started_visuals_unchanged() -> None:
    state = ResearchState()
    state.start_research("1")
    state.mark_research_completed("1")
    assert research_tile_uses_full_color("1", state)
    assert research_tile_image_alpha("1", state) == 255
    assert research_tile_image_alpha("2", state) == 140


def test_active_tile_brighter_than_not_started() -> None:
    surface = pygame.Surface((1280, 720))
    content = compute_content_layout(surface)
    state = ResearchState()
    state.start_research("1")
    draw_research_tiles(surface, content.tiles, research_state=state)
    active_px = surface.get_at(_tile_by_id(content, "1").image_rect.center)
    not_started_px = surface.get_at(_tile_by_id(content, "2").image_rect.center)
    assert sum(active_px[:3]) > sum(not_started_px[:3])


def test_completed_tile_brighter_than_in_progress() -> None:
    surface = pygame.Surface((1280, 720))
    content = compute_content_layout(surface)
    state = ResearchState()
    state.start_research("1")
    state.mark_research_completed("1")
    state.start_research("2")
    draw_research_tiles(surface, content.tiles, research_state=state)
    completed_px = surface.get_at(_tile_by_id(content, "1").image_rect.center)
    active_px = surface.get_at(_tile_by_id(content, "2").image_rect.center)
    assert sum(completed_px[:3]) > sum(active_px[:3])
