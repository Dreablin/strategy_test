"""Tests for building subclasses (type, footprint, income, level caps)."""

import pytest

from game.buildings.farm import Farm
from game.buildings.iron_mine import IronMine
from game.buildings.lumber_camp import LumberCamp
from game.buildings.stone_mine import StoneMine
from game.buildings.town_hall import TownHall


@pytest.mark.parametrize(
    ("cls", "expected_type"),
    [
        (TownHall, "TOWN_HALL"),
        (LumberCamp, "LUMBER_CAMP"),
        (StoneMine, "STONE_MINE"),
        (IronMine, "IRON_MINE"),
        (Farm, "FARM"),
    ],
)
def test_building_type_tag(cls: type, expected_type: str) -> None:
    assert cls.type_tag == expected_type


@pytest.mark.parametrize(
    ("cls", "expected_footprint"),
    [
        (TownHall, (3, 3)),
        (LumberCamp, (2, 2)),
        (StoneMine, (2, 2)),
        (IronMine, (2, 2)),
        (Farm, (2, 2)),
    ],
)
def test_building_footprint(cls: type, expected_footprint: tuple[int, int]) -> None:
    assert cls.footprint == expected_footprint


def test_resource_income_scales_with_level() -> None:
    assert LumberCamp.income(4) == {"wood": 20}
    assert StoneMine.income(3) == {"stone": 15}
    assert IronMine.income(2) == {"iron": 10}
    assert Farm.income(5) == {"food": 25}


def test_town_hall_income_always_empty() -> None:
    assert TownHall.income(1) == {}


def test_resource_building_max_level_10() -> None:
    LumberCamp(level=10)
    with pytest.raises(ValueError):
        LumberCamp(level=11)


def test_town_hall_level_locked_to_one() -> None:
    TownHall(level=1)
    with pytest.raises(ValueError):
        TownHall(level=2)
