"""Tests for Restaurant panel shell (T381)."""

from __future__ import annotations

import pygame

from game.buildings.restaurant import Restaurant
from game.buildings.town_hall import TownHall
from game.ui.restaurant_panel import RestaurantPanel, RestaurantPanelLayout


def _make_restaurant() -> Restaurant:
    r = Restaurant(level=1)
    r.construction_site = None
    return r


def test_restaurant_panel_supports_restaurant() -> None:
    r = _make_restaurant()
    assert RestaurantPanel.supports_building(r)


def test_restaurant_panel_does_not_support_town_hall() -> None:
    th = TownHall(level=1)
    assert not RestaurantPanel.supports_building(th)


def test_restaurant_panel_layout_has_toggle() -> None:
    r = _make_restaurant()
    surface = pygame.Surface((800, 600))
    layout = RestaurantPanel.layout(surface, r, worker_assigned=False)
    assert isinstance(layout, RestaurantPanelLayout)
    assert layout.toggle is not None
    assert layout.toggle.height > 0


def test_restaurant_panel_click_close() -> None:
    r = _make_restaurant()
    surface = pygame.Surface((800, 600))
    layout = RestaurantPanel.layout(surface, r, worker_assigned=False)
    action = RestaurantPanel.click_action(layout.close.center, layout)
    assert action == "close"


def test_restaurant_panel_click_toggle_active() -> None:
    r = _make_restaurant()
    surface = pygame.Surface((800, 600))
    layout = RestaurantPanel.layout(surface, r, worker_assigned=False)
    action = RestaurantPanel.click_action(layout.toggle.center, layout)
    assert action == "toggle_active"


def test_restaurant_panel_toggle_label() -> None:
    r = _make_restaurant()
    assert RestaurantPanel.toggle_label(r) == "Active"
    r.set_active(False)
    assert RestaurantPanel.toggle_label(r) == "Inactive"


def test_restaurant_panel_draw_does_not_crash() -> None:
    r = _make_restaurant()
    surface = pygame.Surface((800, 600))
    layout = RestaurantPanel.draw(surface, r, worker_assigned=False)
    assert layout is not None
