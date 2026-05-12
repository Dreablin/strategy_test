"""Tests for Restaurant panel storage and progress rows (T382)."""

from __future__ import annotations

import pygame

from game.buildings.restaurant import Restaurant
from game.ui.restaurant_panel import RestaurantPanel


def _make_restaurant() -> Restaurant:
    r = Restaurant(level=1)
    r.construction_site = None
    return r


def test_storage_lines_empty() -> None:
    r = _make_restaurant()
    lines = RestaurantPanel.storage_lines(r)
    assert "0" in lines["bread"] and "3" in lines["bread"]
    assert "0" in lines["wine"] and "3" in lines["wine"]
    assert "0" in lines["beef"] and "3" in lines["beef"]
    assert "0" in lines["elite_meal"] and "3" in lines["elite_meal"]


def test_storage_lines_with_stock() -> None:
    r = _make_restaurant()
    r.add_local_storage("bread", 2)
    r.add_local_storage("wine", 1)
    r.add_local_storage("beef", 3)
    r.add_local_storage("elite_meal", 1)
    lines = RestaurantPanel.storage_lines(r)
    assert "2" in lines["bread"]
    assert "1" in lines["wine"]
    assert "3" in lines["beef"]
    assert "1" in lines["elite_meal"]


def test_draw_does_not_crash() -> None:
    r = _make_restaurant()
    surface = pygame.Surface((800, 600))
    layout = RestaurantPanel.draw(surface, r, worker_assigned=False, now_ms=1000)
    assert layout is not None


def test_draw_with_progress_bar() -> None:
    r = _make_restaurant()
    r.processing_started_ms = 100
    r.processing_duration_ms = 1000
    surface = pygame.Surface((800, 600))
    layout = RestaurantPanel.draw(surface, r, worker_assigned=True, now_ms=600)
    assert layout is not None


def test_layout_toggle_not_overlapping_demolish() -> None:
    r = _make_restaurant()
    surface = pygame.Surface((800, 600))
    layout = RestaurantPanel.layout(surface, r, worker_assigned=True)
    if layout.demolish is not None:
        assert layout.toggle.top >= layout.demolish.bottom
