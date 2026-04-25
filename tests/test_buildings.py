"""Tests for building subclasses (type, footprint, income, level caps)."""

import pytest

from game.buildings.farm import Farm
from game.buildings.iron_mine import IronMine
from game.buildings.lumber_camp import LumberCamp
from game.buildings.registry import BuildingRegistry
from game.buildings.stone_mine import StoneMine
from game.buildings.town_hall import TownHall
from game.resources import ResourceManager
from game.world import World


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


def test_upgrade_lumber_camp_spends_cost_and_increments_level() -> None:
    world = World()
    registry = BuildingRegistry(world)
    resources = ResourceManager()
    b = registry.place(LumberCamp, (11, 11))
    resources.add("wood", 500)
    wood_before = resources.get("wood")
    assert registry.upgrade_building(b, resources)
    assert b.level == 2
    assert resources.get("wood") == wood_before - 200


def test_upgrade_rejected_when_insufficient_resources() -> None:
    world = World()
    registry = BuildingRegistry(world)
    resources = ResourceManager()
    b = registry.place(LumberCamp, (12, 12))
    assert resources.try_spend({"wood": resources.get("wood")})
    assert resources.get("wood") == 0
    assert not registry.upgrade_building(b, resources)
    assert b.level == 1


def test_upgrade_rejected_for_town_hall() -> None:
    world = World()
    registry = BuildingRegistry(world)
    resources = ResourceManager()
    th = registry.place(TownHall, (16, 16))
    assert not registry.upgrade_building(th, resources)
    assert th.level == 1


def test_upgrade_updates_per_cycle_when_building_is_staffed() -> None:
    """Staffed production is PRD-accurate; ``sync_resources_per_cycle`` reflects new level after upgrade."""
    world = World()
    registry = BuildingRegistry(world)
    resources = ResourceManager()
    b = registry.place(LumberCamp, (14, 14))
    registry.sync_resources_per_cycle(resources, staffed_buildings={b})
    assert resources.per_cycle["wood"] == 5
    resources.add("wood", 2000)
    assert registry.upgrade_building(b, resources)
    registry.sync_resources_per_cycle(resources, staffed_buildings={b})
    assert resources.per_cycle["wood"] == 10


def test_upgrade_rejected_at_max_level() -> None:
    world = World()
    registry = BuildingRegistry(world)
    resources = ResourceManager()
    resources.add("wood", 60_000)
    resources.add("stone", 60_000)
    resources.add("iron", 60_000)
    b = registry.place(LumberCamp, (18, 18))
    for _ in range(9):
        assert registry.upgrade_building(b, resources)
    assert b.level == 10
    assert not registry.upgrade_building(b, resources)
