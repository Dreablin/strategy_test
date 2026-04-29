"""Tests for building subclasses (type, footprint, income, level caps)."""

import pytest

from game.buildings.farm import Farm
from game.config import town_hall_origin_tile
from game.buildings.iron_mine import IronMine
from game.buildings.lumber_camp import LumberCamp
from game.buildings.registry import BuildingRegistry
from game.buildings.stone_mine import StoneMine
from game.buildings.town_hall import TownHall
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


def test_all_production_buildings_have_no_passive_income() -> None:
    assert LumberCamp.income(1) == {}
    assert LumberCamp.income(5) == {}
    assert StoneMine.income(3) == {}
    assert IronMine.income(2) == {}
    assert Farm.income(5) == {}


def test_town_hall_income_always_empty() -> None:
    assert TownHall.income(1) == {}


def test_resource_building_max_level_10() -> None:
    LumberCamp(level=10)
    with pytest.raises(ValueError):
        LumberCamp(level=11)


def test_town_hall_max_level_10() -> None:
    TownHall(level=10)
    with pytest.raises(ValueError):
        TownHall(level=11)


def test_upgrade_lumber_camp_is_free_and_increments_level() -> None:
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    b = registry.place(LumberCamp, (11, 11))
    assert registry.upgrade_building(b)
    assert b.level == 2


def test_upgrade_no_longer_depends_on_wallet_resources() -> None:
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    b = registry.place(LumberCamp, (12, 12))
    assert registry.upgrade_building(b)
    assert b.level == 2


def test_upgrade_allowed_for_town_hall_below_cap() -> None:
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    th = registry.place(TownHall, town_hall_origin_tile())
    assert registry.upgrade_building(th)
    assert th.level == 2


def test_upgrade_updates_per_cycle_when_building_is_staffed() -> None:
    """No passive per-cycle production should be exposed for active gatherers."""
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    th = registry.place(TownHall, town_hall_origin_tile())
    th.level = 3
    b = registry.place(StoneMine, (10, 10))
    registry.sync_resources_per_cycle(staffed_buildings={b})
    assert registry.upgrade_building(b)
    registry.sync_resources_per_cycle(staffed_buildings={b})


def test_upgrade_rejected_at_max_level() -> None:
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    b = registry.place(LumberCamp, (18, 18))
    for _ in range(9):
        assert registry.upgrade_building(b)
    assert b.level == 10
    assert not registry.upgrade_building(b)


@pytest.mark.parametrize("cls", [LumberCamp, StoneMine, IronMine, Farm])
def test_producing_buildings_expose_storage_api_with_default_state(cls: type) -> None:
    b = cls(level=1, grid_pos=(10, 10))
    assert b.stored == 0
    assert b.storage_capacity() == 3
    assert b.is_storage_full() is False


@pytest.mark.parametrize("cls", [LumberCamp, StoneMine, IronMine, Farm])
def test_storage_capacity_scales_with_level(cls: type) -> None:
    b = cls(level=5, grid_pos=(10, 10))
    assert b.storage_capacity() == 11


@pytest.mark.parametrize("cls", [LumberCamp, StoneMine, IronMine, Farm])
def test_add_to_storage_rejects_negative_and_overflow(cls: type) -> None:
    b = cls(level=1, grid_pos=(10, 10))
    with pytest.raises(ValueError):
        b.add_to_storage(-1)
    b.add_to_storage(3)
    assert b.stored == 3
    assert b.is_storage_full() is True
    with pytest.raises(ValueError):
        b.add_to_storage(1)


@pytest.mark.parametrize("cls", [LumberCamp, StoneMine, IronMine, Farm])
def test_take_from_storage_rejects_overdraw(cls: type) -> None:
    b = cls(level=1, grid_pos=(10, 10))
    b.add_to_storage(2)
    b.take_from_storage(1)
    assert b.stored == 1
    with pytest.raises(ValueError):
        b.take_from_storage(2)


def test_town_hall_exposes_warehouse_api() -> None:
    th = TownHall(level=1, grid_pos=town_hall_origin_tile())
    assert th.warehouse_amount("wood") == 0
    assert th.warehouse_amount("wheat") == 0
    assert th.warehouse_amount("boards") == 0
    th.add_to_warehouse("wood", 2)
    th.add_to_warehouse("food", 1)
    th.add_to_warehouse("boards", 3)
    assert th.warehouse_amount("wood") == 2
    assert th.warehouse_amount("wheat") == 1
    assert th.warehouse_amount("boards") == 3
    th.take_from_warehouse("wood", 1)
    assert th.warehouse_amount("wood") == 1
