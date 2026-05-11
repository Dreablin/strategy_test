"""Tests for Winery wine output export planning (T352)."""

from __future__ import annotations

from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.buildings.winery import Winery
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.construction import ConstructionSite
from game.transport_tasks import winery_output_transport_tasks
from game.world import World


def test_winery_output_tasks_one_per_stored_wine() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    winery = registry.place(Winery, near_town_hall_tile(10, 10))
    winery.construction_site = None
    winery.add_wine(2)

    tasks = winery_output_transport_tasks(registry)
    assert len(tasks) == 2
    assert all(t.resource == "wine" for t in tasks)
    assert all(t.source is winery for t in tasks)
    assert all(t.target is town_hall for t in tasks)


def test_winery_output_tasks_empty_when_no_wine() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    winery = registry.place(Winery, near_town_hall_tile(10, 10))
    winery.construction_site = None

    tasks = winery_output_transport_tasks(registry)
    assert tasks == []


def test_winery_output_tasks_skip_inactive() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    winery = registry.place(Winery, near_town_hall_tile(10, 10))
    winery.construction_site = None
    winery.add_wine(1)
    winery.set_active(False)

    tasks = winery_output_transport_tasks(registry)
    assert tasks == []


def test_winery_output_tasks_skip_under_construction() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    winery = registry.place(Winery, near_town_hall_tile(10, 10))
    winery.construction_site = ConstructionSite(
        required_resources={"wood": 3, "stone": 2},
        delivered_resources={},
        build_time_ms=45_000,
        build_started_ms=None,
        builder=None,
        target_level=1,
    )
    winery.wine_out = 2

    tasks = winery_output_transport_tasks(registry)
    assert tasks == []
