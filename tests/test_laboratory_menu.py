"""Tests for Laboratory in Social build menu (T397)."""

from __future__ import annotations

import pygame

from game.ui.bottom_bar import BottomBar, BUILD_MENU_SELECT


def test_social_menu_includes_laboratory_entry() -> None:
    BottomBar._menu = "social"
    surface = pygame.Surface((1200, 80))
    BottomBar.draw(surface)
    assert BottomBar._menu == "social"


def test_social_menu_click_laboratory_emits_event() -> None:
    BottomBar._menu = "social"
    surface = pygame.Surface((1200, 80))
    BottomBar.draw(surface)

    from game.ui.bottom_bar import _button_rects

    entries = ("back", "school", "house", "canteen", "restaurant", "laboratory", "statue")
    rects = _button_rects(surface, len(entries))
    laboratory_rect = rects[5]
    center = laboratory_rect.center

    pygame.event.clear()
    BottomBar.handle_click(surface, center)
    events = [event for event in pygame.event.get() if event.type == BUILD_MENU_SELECT]
    assert len(events) == 1
    assert events[0].building_type == "LABORATORY"
