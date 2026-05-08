"""RED tests for the Canteen building domain (T246)."""

from __future__ import annotations

import pytest

from game import config
from game.buildings.canteen import Canteen
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.world import World


def test_canteen_type_footprint_and_levels() -> None:
    assert Canteen.type_tag == "CANTEEN"
    assert Canteen.footprint == (2, 2)
    assert Canteen.max_level() == 10
    Canteen(level=10)
    with pytest.raises(ValueError):
        Canteen(level=11)


def test_registry_places_canteen_and_blocks_overlap() -> None:
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    pos = near_town_hall_tile(8, 8)

    canteen = registry.place(Canteen, pos)

    assert canteen.type_tag == "CANTEEN"
    assert not registry.can_place(Canteen, pos)
    with pytest.raises(ValueError):
        registry.place(Canteen, pos)


def test_canteen_construction_requirements_are_configured_for_levels_1_to_10() -> None:
    levels = config.CONSTRUCTION_REQUIREMENTS["CANTEEN"]

    assert set(levels) == set(range(1, 11))
    for spec in levels.values():
        assert spec.build_time_ms > 0
        assert any(amount > 0 for amount in spec.cost.values())


def test_canteen_local_storage_buckets_start_empty_and_capacity_scales_by_level() -> None:
    canteen = Canteen(level=1)

    assert canteen.local_storage_resources() == ("chicken", "bread", "water", "simple_meal")
    for resource in canteen.local_storage_resources():
        assert canteen.local_storage_amount(resource) == 0
        assert canteen.local_storage_capacity(resource) == 5

    upgraded = Canteen(level=4)
    for resource in upgraded.local_storage_resources():
        assert upgraded.local_storage_capacity(resource) == 8


def test_canteen_local_storage_helpers_enforce_bucket_capacity() -> None:
    canteen = Canteen(level=1)

    canteen.add_local_storage("chicken", 5)
    assert canteen.local_storage_amount("chicken") == 5
    with pytest.raises(ValueError):
        canteen.add_local_storage("chicken", 1)

    canteen.take_local_storage("chicken", 2)
    assert canteen.local_storage_amount("chicken") == 3
    with pytest.raises(ValueError):
        canteen.take_local_storage("chicken", 4)


def test_canteen_rejects_unknown_local_storage_resource() -> None:
    canteen = Canteen(level=1)

    with pytest.raises(KeyError):
        canteen.local_storage_amount("wood")
    with pytest.raises(KeyError):
        canteen.add_local_storage("wood", 1)


def test_canteen_diner_slot_capacity_scales_by_level() -> None:
    assert Canteen(level=1).diner_slot_capacity() == 3
    assert Canteen(level=4).diner_slot_capacity() == 6
    assert Canteen(level=10).diner_slot_capacity() == 12
