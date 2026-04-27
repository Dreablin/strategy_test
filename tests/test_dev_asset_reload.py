"""Smoke tests for temporary asset reload dev button."""

import pygame

from game import dev_asset_reload


def test_button_rect_within_top_bar() -> None:
    surface = pygame.Surface((800, 600))
    rect = dev_asset_reload.button_rect(surface)
    assert rect.top >= 0
    assert rect.bottom <= 48
    assert rect.right <= surface.get_width()


def test_handle_click_posts_reload_event() -> None:
    surface = pygame.Surface((800, 600))
    rect = dev_asset_reload.button_rect(surface)
    pygame.event.clear()
    assert dev_asset_reload.handle_click(surface, rect.center)
    assert any(e.type == dev_asset_reload.ASSET_RELOAD_REQUEST for e in pygame.event.get())
