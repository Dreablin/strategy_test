"""Tests for ResourceManager (food, wood, stone, iron)."""

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


def test_has_true_when_sufficient() -> None:
    rm = ResourceManager()
    assert rm.has({"food": 200, "wood": 100})


def test_has_false_when_insufficient() -> None:
    rm = ResourceManager()
    assert not rm.has({"food": 201})


def test_try_spend_success_deducts() -> None:
    rm = ResourceManager()
    assert rm.try_spend({"wood": 100, "food": 50})
    assert rm.get("wood") == 100
    assert rm.get("food") == 150


def test_try_spend_failure_no_deduction() -> None:
    rm = ResourceManager()
    before = {k: rm.get(k) for k in ("food", "wood", "stone", "iron")}
    assert not rm.try_spend({"wood": 500})
    for k, v in before.items():
        assert rm.get(k) == v


def test_try_spend_partial_insufficient_no_deduction() -> None:
    """If any line in cost is unmet, nothing is spent."""
    rm = ResourceManager()
    assert not rm.try_spend({"wood": 50, "iron": 1})
    assert rm.get("wood") == 200
    assert rm.get("iron") == 0


def test_non_negative_after_add() -> None:
    rm = ResourceManager()
    rm.add("stone", -5)
    assert rm.get("stone") >= 0


def test_per_cycle_property_exists() -> None:
    rm = ResourceManager()
    assert isinstance(rm.per_cycle, dict)
