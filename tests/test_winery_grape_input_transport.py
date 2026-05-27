"""Tests for Winery grape input transport planning (T351)."""

from __future__ import annotations

from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.buildings.winery import Winery
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.construction import ConstructionSite
from game.transport_tasks import winery_input_transport_tasks
from game.world import World


def test_winery_input_tasks_one_per_unit_of_free_capacity() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    winery = registry.place(Winery, near_town_hall_tile(10, 10))
    winery.construction_site = None
    town_hall.add_to_warehouse("grapes", winery.input_capacity())

    tasks = winery_input_transport_tasks(registry)
    assert len(tasks) == winery.input_capacity()
    assert all(t.resource == "grapes" for t in tasks)
    assert all(t.source is town_hall for t in tasks)
    assert all(t.target is winery for t in tasks)


def test_winery_input_tasks_limited_by_town_hall_stock() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    town_hall.add_to_warehouse("grapes", 2)
    winery = registry.place(Winery, near_town_hall_tile(10, 10))
    winery.construction_site = None

    tasks = winery_input_transport_tasks(registry)
    assert len(tasks) == 2


def test_winery_input_tasks_skip_inactive_winery() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    winery = registry.place(Winery, near_town_hall_tile(10, 10))
    winery.construction_site = None
    town_hall.add_to_warehouse("grapes", winery.input_capacity())
    winery.set_active(False)

    tasks = winery_input_transport_tasks(registry)
    assert tasks == []


def test_winery_input_tasks_skip_under_construction() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    winery = registry.place(Winery, near_town_hall_tile(10, 10))
    town_hall.add_to_warehouse("grapes", winery.input_capacity())
    winery.construction_site = ConstructionSite(
        required_resources={"wood": 3, "stone": 2},
        delivered_resources={},
        build_time_ms=45_000,
        build_started_ms=None,
        builder=None,
        target_level=1,
    )

    tasks = winery_input_transport_tasks(registry)
    assert tasks == []


def test_winery_input_tasks_skip_full_winery() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    winery = registry.place(Winery, near_town_hall_tile(10, 10))
    winery.construction_site = None
    town_hall.add_to_warehouse("grapes", winery.input_capacity())
    winery.add_grapes(winery.input_capacity())

    tasks = winery_input_transport_tasks(registry)
    assert tasks == []


def test_winery_input_tasks_empty_when_no_grapes_in_town_hall() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    winery = registry.place(Winery, near_town_hall_tile(10, 10))
    winery.construction_site = None

    tasks = winery_input_transport_tasks(registry)
    assert tasks == []
