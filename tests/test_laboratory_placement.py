"""Tests for Laboratory placement/construction registration (T394)."""

from __future__ import annotations

from game.buildings.laboratory import Laboratory
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.config import CONSTRUCTION_REQUIREMENTS, near_town_hall_tile, town_hall_origin_tile
from game.ui.placement import PlacementController
from game.world import World


def test_laboratory_in_placement_tag_to_class() -> None:
    from game.ui.placement import _TAG_TO_CLASS

    assert "LABORATORY" in _TAG_TO_CLASS
    assert _TAG_TO_CLASS["LABORATORY"] is Laboratory


def test_laboratory_can_be_placed_via_registry() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    laboratory = registry.place(Laboratory, near_town_hall_tile(10, 10))
    assert laboratory is not None
    assert laboratory.type_tag == "LABORATORY"
    assert laboratory.grid_pos == near_town_hall_tile(10, 10)


def test_laboratory_construction_requirements_exist() -> None:
    assert "LABORATORY" in CONSTRUCTION_REQUIREMENTS
    specs = CONSTRUCTION_REQUIREMENTS["LABORATORY"]
    assert 1 in specs
    assert specs[1].cost
    assert specs[1].build_time_ms > 0


def test_laboratory_placement_controller_select() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    placement = PlacementController(world, registry)
    placement.select("LABORATORY")
    assert placement.has_pending
    assert placement.pending_type is Laboratory


def test_laboratory_starts_under_construction() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    laboratory = registry.place(Laboratory, near_town_hall_tile(8, 8))
    assert laboratory.is_under_construction is True
