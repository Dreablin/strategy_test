"""Tests for Restaurant panel diner tiles (T383)."""

from __future__ import annotations

from game.buildings.restaurant import Restaurant
from game.canteen_dining import try_reserve_diner_slot_and_meal
from game.ui.restaurant_panel import RestaurantPanel
from game.worker_models import Worker


def _make_restaurant() -> Restaurant:
    r = Restaurant(level=1)
    r.construction_site = None
    return r


def _make_worker(type_tag: str = "WINEMAKER") -> Worker:
    w = Worker(type_tag=type_tag)
    w.satiety = 0
    return w


def test_diner_visual_state_empty() -> None:
    r = _make_restaurant()
    state = RestaurantPanel.diner_visual_state(r, 0)
    assert state == "empty"


def test_diner_visual_state_walking() -> None:
    r = _make_restaurant()
    r.add_local_storage("elite_meal", 1)
    w = _make_worker()
    try_reserve_diner_slot_and_meal(r, w)
    w.dining_phase = "walking_to_diner"
    state = RestaurantPanel.diner_visual_state(r, 0)
    assert state == "walking"


def test_diner_visual_state_waiting() -> None:
    r = _make_restaurant()
    r.add_local_storage("elite_meal", 1)
    w = _make_worker()
    try_reserve_diner_slot_and_meal(r, w)
    w.dining_phase = "waiting_for_meal"
    state = RestaurantPanel.diner_visual_state(r, 0)
    assert state == "waiting"


def test_diner_visual_state_eating() -> None:
    r = _make_restaurant()
    r.add_local_storage("elite_meal", 1)
    w = _make_worker()
    try_reserve_diner_slot_and_meal(r, w)
    w.dining_phase = "eating"
    state = RestaurantPanel.diner_visual_state(r, 0)
    assert state == "eating"
