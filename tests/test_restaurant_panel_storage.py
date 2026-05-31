"""Tests for Restaurant panel storage and progress rows (T382)."""

from __future__ import annotations

import pygame

from game import i18n
from game.buildings.restaurant import Restaurant
from game.ui.restaurant_panel import RestaurantPanel


def _make_restaurant() -> Restaurant:
    r = Restaurant(level=1)
    r.construction_site = None
    return r


def test_storage_lines_empty() -> None:
    r = _make_restaurant()
    lines = RestaurantPanel.storage_lines(r)
    for resource in ("bread", "wine", "beef", "elite_meal"):
        assert i18n.t(f"resource.{resource}") in lines[resource]
        assert f"0 / {r.local_storage_capacity(resource)}" in lines[resource]


def test_storage_lines_with_stock() -> None:
    r = _make_restaurant()
    r.add_local_storage("bread", 2)
    r.add_local_storage("wine", 1)
    beef_amount = min(3, r.local_storage_capacity("beef"))
    r.add_local_storage("beef", beef_amount)
    r.add_local_storage("elite_meal", 1)
    lines = RestaurantPanel.storage_lines(r)
    assert "2" in lines["bread"]
    assert "1" in lines["wine"]
    assert str(beef_amount) in lines["beef"]
    assert "1" in lines["elite_meal"]


def test_layout_toggle_not_overlapping_demolish() -> None:
    r = _make_restaurant()
    surface = pygame.Surface((800, 600))
    layout = RestaurantPanel.layout(surface, r, worker_assigned=True)
    if layout.demolish is not None:
        assert layout.toggle.top >= layout.demolish.bottom
