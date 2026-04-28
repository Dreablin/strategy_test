"""Tests for ResourceManager (food, wood, stone, iron, boards)."""

from game.config import INITIAL_RESOURCES
from game.resources import ResourceManager


def test_initial_values() -> None:
    rm = ResourceManager()
    for name, expected in INITIAL_RESOURCES.items():
        assert rm.get(name) == expected


def test_add_increments() -> None:
    rm = ResourceManager()
    rm.add("wood", 50)
    assert rm.get("wood") == 250
    rm.add("stone", 10)
    assert rm.get("stone") == 10
    rm.add("boards", 4)
    assert rm.get("boards") == 4


def test_non_negative_after_add() -> None:
    rm = ResourceManager()
    rm.add("stone", -5)
    assert rm.get("stone") >= 0


def test_per_cycle_property_exists() -> None:
    rm = ResourceManager()
    assert isinstance(rm.per_cycle, dict)


def test_wheat_alias_points_to_food_storage() -> None:
    rm = ResourceManager()
    before = rm.get("food")
    rm.add("wheat", 3)
    assert rm.get("food") == before + 3
    assert rm.get("wheat") == before + 3
    rm.add("wheat", -2)
    assert rm.get("food") == before + 1
