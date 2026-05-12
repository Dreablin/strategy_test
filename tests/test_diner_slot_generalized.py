"""Tests for generalized diner slot reservation helpers (T362)."""

from __future__ import annotations

from game.buildings.canteen import Canteen
from game.canteen_dining import (
    available_meals_for_reservation,
    count_reserved_diner_slots,
    count_reserved_meals,
    release_all_diner_slots_for_building,
    release_diner_slot_after_meal,
    release_diner_slots_for_worker,
    try_reserve_diner_slot,
    try_reserve_diner_slot_and_meal,
)
from game.worker_models import Worker


def _make_worker(type_tag: str = "BAKER") -> Worker:
    w = Worker(type_tag=type_tag)
    w.satiety = 0
    return w


def test_canteen_has_meal_resource_key() -> None:
    c = Canteen(level=1)
    assert c.meal_resource_key() == "simple_meal"


def test_reserve_slot_uses_duck_typing_interface() -> None:
    c = Canteen(level=1)
    w = _make_worker()
    assert try_reserve_diner_slot(c, w)
    assert count_reserved_diner_slots(c) == 1
    assert w.dining_canteen is c


def test_reserve_slot_and_meal_uses_meal_resource_key() -> None:
    c = Canteen(level=1)
    c.add_local_storage("simple_meal", 1)
    w = _make_worker()
    assert try_reserve_diner_slot_and_meal(c, w)
    assert count_reserved_meals(c) == 1
    assert w.dining_meal_reserved is True


def test_available_meals_reads_meal_resource_key() -> None:
    c = Canteen(level=1)
    assert available_meals_for_reservation(c) == 0
    c.add_local_storage("simple_meal", 2)
    assert available_meals_for_reservation(c) == 2


def test_release_slot_after_meal_generic() -> None:
    c = Canteen(level=1)
    c.add_local_storage("simple_meal", 1)
    w = _make_worker()
    try_reserve_diner_slot_and_meal(c, w)
    release_diner_slot_after_meal(c, w)
    assert count_reserved_diner_slots(c) == 0
    assert w.dining_canteen is None


def test_release_slots_for_worker_generic() -> None:
    c = Canteen(level=1)
    c.add_local_storage("simple_meal", 1)
    w = _make_worker()
    try_reserve_diner_slot_and_meal(c, w)
    release_diner_slots_for_worker(w)
    assert count_reserved_diner_slots(c) == 0
    assert w.dining_canteen is None


def test_release_all_slots_for_building_generic() -> None:
    c = Canteen(level=1)
    c.add_local_storage("simple_meal", 2)
    w1 = _make_worker()
    w2 = _make_worker()
    try_reserve_diner_slot_and_meal(c, w1)
    try_reserve_diner_slot_and_meal(c, w2)
    release_all_diner_slots_for_building(c)
    assert count_reserved_diner_slots(c) == 0
    assert w1.dining_canteen is None
    assert w2.dining_canteen is None


def test_no_double_reservation() -> None:
    c = Canteen(level=1)
    c.add_local_storage("simple_meal", 2)
    w = _make_worker()
    assert try_reserve_diner_slot_and_meal(c, w)
    assert not try_reserve_diner_slot_and_meal(c, w)
