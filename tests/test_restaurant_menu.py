"""Tests for Restaurant in Social build menu (T369)."""

from __future__ import annotations

import pygame

from game.ui.bottom_bar import BottomBar, BUILD_MENU_SELECT


def test_social_menu_includes_restaurant_entry() -> None:
    BottomBar._menu = "social"
    surface = pygame.Surface((1200, 80))
    BottomBar.draw(surface)
    assert BottomBar._menu == "social"


def test_social_menu_click_restaurant_emits_event() -> None:
    BottomBar._menu = "social"
    surface = pygame.Surface((1200, 80))
    BottomBar.draw(surface)

    from game.ui.bottom_bar import _button_rects
    entries = ("back", "school", "house", "canteen", "restaurant", "laboratory")
    rects = _button_rects(surface, len(entries))
    restaurant_rect = rects[entries.index("restaurant")]
    center = restaurant_rect.center

    pygame.event.clear()
    BottomBar.handle_click(surface, center)
    events = [e for e in pygame.event.get() if e.type == BUILD_MENU_SELECT]
    assert len(events) == 1
    assert events[0].building_type == "RESTAURANT"
