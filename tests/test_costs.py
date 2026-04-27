"""Tests for building construction and upgrade cost tables."""

import pytest

from game.buildings.costs import upgrade_cost


def test_upgrade_cost_l1_to_l2() -> None:
    assert upgrade_cost(1) == {"wood": 5}


def test_upgrade_cost_l3_to_l4_wood_only() -> None:
    assert upgrade_cost(3) == {"wood": 5}


def test_upgrade_cost_l4_to_l5_adds_stone() -> None:
    assert upgrade_cost(4) == {"wood": 5, "stone": 5}


def test_upgrade_cost_l5_to_l6() -> None:
    assert upgrade_cost(5) == {"wood": 5, "stone": 5}


def test_upgrade_cost_l6_to_l7_adds_iron() -> None:
    assert upgrade_cost(6) == {"wood": 5, "stone": 5, "iron": 5}


def test_upgrade_cost_l9_to_l10() -> None:
    assert upgrade_cost(9) == {"wood": 5, "stone": 5, "iron": 5}


def test_upgrade_past_max_level_raises() -> None:
    with pytest.raises(ValueError):
        upgrade_cost(10)
