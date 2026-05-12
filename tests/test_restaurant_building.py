"""Tests for Restaurant building class shell (T366)."""

from __future__ import annotations

import pytest

from game.buildings.restaurant import Restaurant


def test_restaurant_type_tag() -> None:
    r = Restaurant(level=1)
    assert r.type_tag == "RESTAURANT"


def test_restaurant_active_default() -> None:
    r = Restaurant(level=1)
    assert r.active is True


def test_restaurant_set_active() -> None:
    r = Restaurant(level=1)
    r.set_active(False)
    assert r.active is False


def test_restaurant_local_storage_resources() -> None:
    r = Restaurant(level=1)
    assert r.local_storage_resources() == ("bread", "wine", "beef", "elite_meal")


def test_restaurant_local_storage_capacity() -> None:
    r = Restaurant(level=1)
    assert r.local_storage_capacity("bread") == 3


def test_restaurant_add_and_take_local_storage() -> None:
    r = Restaurant(level=1)
    r.add_local_storage("bread", 2)
    assert r.local_storage_amount("bread") == 2
    r.take_local_storage("bread", 1)
    assert r.local_storage_amount("bread") == 1


def test_restaurant_local_storage_overflow() -> None:
    r = Restaurant(level=1)
    with pytest.raises(ValueError, match="overflow"):
        r.add_local_storage("bread", 100)


def test_restaurant_local_storage_insufficient() -> None:
    r = Restaurant(level=1)
    with pytest.raises(ValueError, match="insufficient"):
        r.take_local_storage("bread", 1)


def test_restaurant_diner_slot_capacity() -> None:
    r = Restaurant(level=1)
    assert r.diner_slot_capacity() == 2


def test_restaurant_meal_resource_key() -> None:
    r = Restaurant(level=1)
    assert r.meal_resource_key() == "elite_meal"


def test_restaurant_dining_tier() -> None:
    r = Restaurant(level=1)
    assert r.dining_tier() == "advanced"


def test_restaurant_recipe_input() -> None:
    r = Restaurant(level=1)
    assert r.recipe_input() == {"bread": 1, "wine": 1, "beef": 1}


def test_restaurant_recipe_output() -> None:
    r = Restaurant(level=1)
    assert r.recipe_output() == {"elite_meal": 1}


def test_restaurant_has_recipe_inputs_false_empty() -> None:
    r = Restaurant(level=1)
    assert r.has_recipe_inputs() is False


def test_restaurant_has_recipe_inputs_true() -> None:
    r = Restaurant(level=1)
    r.add_local_storage("bread", 1)
    r.add_local_storage("wine", 1)
    r.add_local_storage("beef", 1)
    assert r.has_recipe_inputs() is True


def test_restaurant_output_amount_and_capacity() -> None:
    r = Restaurant(level=1)
    assert r.output_amount() == 0
    assert r.output_capacity() == 3
    r.add_local_storage("elite_meal", 2)
    assert r.output_amount() == 2


def test_restaurant_cycle_ms() -> None:
    r = Restaurant(level=1)
    assert r.cycle_ms() == 45000


def test_restaurant_rest_ms() -> None:
    r = Restaurant(level=1)
    assert r.rest_ms() == 8000


def test_restaurant_processing_progress() -> None:
    r = Restaurant(level=1)
    assert r.processing_progress(1000) == 0.0
    r.processing_started_ms = 100
    r.processing_duration_ms = 1000
    assert r.processing_progress(600) == pytest.approx(0.5, abs=0.01)


def test_restaurant_invalid_resource_raises() -> None:
    r = Restaurant(level=1)
    with pytest.raises(KeyError):
        r.local_storage_amount("invalid_resource")
