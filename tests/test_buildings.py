"""Tests for building subclasses (type, footprint, income, level caps)."""

import pytest

from game.construction import ConstructionSite
from game.buildings.farm import Farm
from game.buildings.chicken_farm import ChickenFarm
from game.config import building_level_int_setting, town_hall_origin_tile
from game.buildings.iron_mine import IronMine
from game.buildings.lumber_camp import LumberCamp
from game.buildings.mill import Mill
from game.buildings.registry import BuildingRegistry
from game.buildings.stone_mine import StoneMine
from game.buildings.town_hall import TownHall
from game.buildings.well import Well
from game.world import World


@pytest.mark.parametrize(
    ("cls", "expected_type"),
    [
        (TownHall, "TOWN_HALL"),
        (LumberCamp, "LUMBER_CAMP"),
        (StoneMine, "STONE_MINE"),
        (IronMine, "IRON_MINE"),
        (Farm, "FARM"),
        (ChickenFarm, "CHICKEN_FARM"),
        (Mill, "MILL"),
        (Well, "WELL"),
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
        (ChickenFarm, (2, 2)),
        (Mill, (2, 2)),
        (Well, (1, 1)),
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
    assert ChickenFarm.income(5) == {}
    assert Mill.income(5) == {}
    assert Well.income(1) == {}


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


def test_well_max_level_10() -> None:
    Well(level=10)
    with pytest.raises(ValueError):
        Well(level=11)


def test_upgrade_lumber_camp_starts_construction_to_level_2() -> None:
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    b = registry.place(LumberCamp, (11, 11))
    b.construction_site = None
    assert registry.upgrade_building(b)
    assert b.level == 1
    assert b.is_under_construction
    assert b.construction_site is not None
    assert b.construction_site.target_level == 2


def test_upgrade_no_longer_depends_on_wallet_resources_and_starts_construction() -> None:
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    b = registry.place(LumberCamp, (12, 12))
    b.construction_site = None
    assert registry.upgrade_building(b)
    assert b.level == 1
    assert b.is_under_construction


def test_upgrade_allowed_for_town_hall_below_cap() -> None:
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    th = registry.place(TownHall, town_hall_origin_tile())
    assert registry.upgrade_building(th)
    assert th.level == 2


def test_upgrade_succeeds_for_stone_mine_with_town_hall_tech_gate_and_starts_construction() -> None:
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    th = registry.place(TownHall, town_hall_origin_tile())
    th.level = 3
    b = registry.place(StoneMine, (10, 10))
    b.construction_site = None
    assert registry.upgrade_building(b)
    assert b.level == 1
    assert b.is_under_construction
    assert b.construction_site is not None
    assert b.construction_site.target_level == 2


def test_upgrade_rejected_at_max_level() -> None:
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    b = registry.place(TownHall, town_hall_origin_tile())
    for _ in range(9):
        assert registry.upgrade_building(b)
    assert b.level == 10
    assert not registry.upgrade_building(b)


@pytest.mark.parametrize("cls", [LumberCamp, StoneMine, IronMine, Farm, Well])
def test_producing_buildings_expose_storage_api_with_default_state(cls: type) -> None:
    b = cls(level=1, grid_pos=(10, 10))
    assert b.stored == 0
    assert b.storage_capacity() == building_level_int_setting(b.type_tag, "storage", 1)
    assert b.is_storage_full() is False


@pytest.mark.parametrize("cls", [LumberCamp, StoneMine, IronMine, Well])
def test_storage_capacity_scales_with_level(cls: type) -> None:
    b = cls(level=5, grid_pos=(10, 10))
    assert b.storage_capacity() == building_level_int_setting(b.type_tag, "storage", 5)


@pytest.mark.parametrize("cls", [LumberCamp, StoneMine, IronMine, Farm, Well])
def test_add_to_storage_rejects_negative_and_overflow(cls: type) -> None:
    b = cls(level=1, grid_pos=(10, 10))
    cap = b.storage_capacity()
    with pytest.raises(ValueError):
        b.add_to_storage(-1)
    b.add_to_storage(cap)
    assert b.stored == cap
    assert b.is_storage_full() is True
    with pytest.raises(ValueError):
        b.add_to_storage(1)


@pytest.mark.parametrize("cls", [LumberCamp, StoneMine, IronMine, Farm, Well])
def test_take_from_storage_rejects_overdraw(cls: type) -> None:
    b = cls(level=1, grid_pos=(10, 10))
    initial = min(2, b.storage_capacity())
    if initial > 0:
        b.add_to_storage(initial)
    if initial > 1:
        b.take_from_storage(1)
        assert b.stored == initial - 1
    with pytest.raises(ValueError):
        b.take_from_storage(initial + 1)


def test_town_hall_exposes_warehouse_api() -> None:
    th = TownHall(level=1, grid_pos=town_hall_origin_tile())
    assert th.warehouse_amount("wood") == 0
    assert th.warehouse_amount("wheat") == 0
    assert th.warehouse_amount("boards") == 0
    assert th.warehouse_amount("flour") == 0
    assert th.warehouse_amount("chicken") == 0
    th.add_to_warehouse("wood", 2)
    th.add_to_warehouse("wheat", 1)
    th.add_to_warehouse("boards", 3)
    th.add_to_warehouse("flour", 4)
    th.add_to_warehouse("chicken", 5)
    assert th.warehouse_amount("wood") == 2
    assert th.warehouse_amount("wheat") == 1
    assert th.warehouse_amount("boards") == 3
    assert th.warehouse_amount("flour") == 4
    assert th.warehouse_amount("chicken") == 5
    th.take_from_warehouse("wood", 1)
    assert th.warehouse_amount("wood") == 1


def test_well_exposes_local_water_storage_api() -> None:
    well = Well(level=3, grid_pos=(10, 10))
    assert well.local_storage_resources() == ("water",)
    assert well.local_storage_capacity("water") == building_level_int_setting("WELL", "storage", 3)
    assert well.water_amount() == 0
    assert well.water_capacity() == well.storage_capacity()
    assert well.output_amount() == 0
    assert well.output_capacity() == well.storage_capacity()
    well.add_water_in(2)
    assert well.water_amount() == 2
    well.take_water_in(1)
    assert well.water_amount() == 1
    with pytest.raises(KeyError):
        well.local_storage_amount("wood")


@pytest.mark.parametrize("cls", [LumberCamp, StoneMine, IronMine, Farm, ChickenFarm, TownHall, Well])
def test_buildings_default_to_not_under_construction(cls: type) -> None:
    building = cls(level=1, grid_pos=(10, 10))
    assert building.construction_site is None
    assert building.is_under_construction is False


def test_chicken_farm_storage_and_level_caps() -> None:
    farm = ChickenFarm(level=1, grid_pos=(10, 10))
    expected_l1 = building_level_int_setting("CHICKEN_FARM", "storage", 1)
    assert farm.input_capacity() == expected_l1
    assert farm.water_capacity() == expected_l1
    assert farm.output_capacity() == expected_l1
    assert ChickenFarm(level=2, grid_pos=(10, 10)).input_capacity() == building_level_int_setting(
        "CHICKEN_FARM", "storage", 2
    )
    assert ChickenFarm(level=3, grid_pos=(10, 10)).output_capacity() == building_level_int_setting(
        "CHICKEN_FARM", "storage", 3
    )
    assert ChickenFarm(level=10, grid_pos=(10, 10)).water_capacity() == building_level_int_setting(
        "CHICKEN_FARM", "storage", 10
    )


def test_chicken_farm_max_level_10() -> None:
    ChickenFarm(level=10)
    with pytest.raises(ValueError):
        ChickenFarm(level=11)


def test_building_reports_under_construction_when_site_is_set() -> None:
    camp = LumberCamp(level=1, grid_pos=(10, 10))
    camp.construction_site = ConstructionSite(
        required_resources={"wood": 2},
        delivered_resources={},
        build_time_ms=20_000,
        build_started_ms=None,
        builder=None,
        target_level=2,
    )
    assert camp.is_under_construction is True
    # Existing subclass fields/methods still behave with construction_site present.
    camp.add_to_storage(1)
    assert camp.stored == 1
