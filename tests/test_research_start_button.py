"""Per-tile Start button layout and rendering tests (T413)."""

from __future__ import annotations

import pygame

from game.ui.research_screen_layout import compute_content_layout
from game.ui.research_start_button import draw_research_start_button
from game.ui.research_tiles import draw_research_tiles


def test_start_button_is_below_title_with_gap() -> None:
    surface = pygame.Surface((1280, 720))
    content = compute_content_layout(surface)
    for tile in content.tiles:
        assert tile.start_button.top >= tile.title_rect.bottom + 4
        assert tile.tile_rect.contains(tile.start_button)


def test_start_button_fits_inside_tile_slot() -> None:
    surface = pygame.Surface((1280, 720))
    content = compute_content_layout(surface)
    for tile in content.tiles:
        assert tile.tile_rect.contains(tile.start_button)
        assert tile.start_button.width >= 48
        assert tile.start_button.height >= 20


def test_draw_enabled_and_disabled_buttons_differ() -> None:
    surface = pygame.Surface((200, 80))
    enabled_rect = pygame.Rect(10, 10, 72, 24)
    disabled_rect = pygame.Rect(100, 10, 72, 24)
    draw_research_start_button(surface, enabled_rect, enabled=True)
    enabled_px = surface.get_at(enabled_rect.center)
    surface.fill((28, 32, 40))
    draw_research_start_button(surface, disabled_rect, enabled=False)
    disabled_px = surface.get_at(disabled_rect.center)
    assert enabled_px[:3] != disabled_px[:3]
    assert sum(enabled_px[:3]) > sum(disabled_px[:3])


def test_draw_research_tiles_uses_eligibility_flags() -> None:
    surface = pygame.Surface((1280, 720))
    content = compute_content_layout(surface)
    draw_research_tiles(
        surface,
        content.tiles,
        research_can_start={"1": True, "2": False, "3": False, "4": False},
    )
    tile1 = next(t for t in content.tiles if t.research_id == "1")
    tile2 = next(t for t in content.tiles if t.research_id == "2")
    enabled_px = surface.get_at(tile1.start_button.center)
    disabled_px = surface.get_at(tile2.start_button.center)
    assert sum(enabled_px[:3]) > sum(disabled_px[:3])


def test_default_eligibility_disables_all_start_buttons() -> None:
    surface = pygame.Surface((1280, 720))
    content = compute_content_layout(surface)
    draw_research_tiles(surface, content.tiles)
    tile = content.tiles[0]
    corner = (tile.start_button.left + 3, tile.start_button.top + 3)
    px = surface.get_at(corner)
    assert sum(px[:3]) < 200
