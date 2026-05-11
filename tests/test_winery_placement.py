"""Tests for Winery placement/construction registration (T347)."""

from __future__ import annotations

from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.buildings.winery import Winery
from game.config import CONSTRUCTION_REQUIREMENTS, near_town_hall_tile, town_hall_origin_tile
from game.ui.placement import PlacementController
from game.world import World


def test_winery_in_placement_controller_tag_to_class() -> None:
    from game.ui.placement import _TAG_TO_CLASS

    assert "WINERY" in _TAG_TO_CLASS
    assert _TAG_TO_CLASS["WINERY"] is Winery


def test_winery_can_be_placed_via_registry() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    winery = registry.place(Winery, near_town_hall_tile(10, 10))
    assert winery is not None
    assert winery.type_tag == "WINERY"
    assert winery.grid_pos == near_town_hall_tile(10, 10)


def test_winery_construction_requirements_exist() -> None:
    assert "WINERY" in CONSTRUCTION_REQUIREMENTS
    specs = CONSTRUCTION_REQUIREMENTS["WINERY"]
    assert 1 in specs
    assert specs[1].cost == {"wood": 3, "stone": 2}
    assert specs[1].build_time_ms == 45_000


def test_winery_placement_controller_select() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    placement = PlacementController(world, registry)
    placement.select("WINERY")
    assert placement.has_pending
    assert placement.pending_type is Winery
