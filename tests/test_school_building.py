"""School building registration and placement."""

from game.ui.placement import _TAG_TO_CLASS
from game.world import World
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.config import town_hall_origin_tile, near_town_hall_tile


def test_school_registered_in_placement_tags() -> None:
    assert "SCHOOL" in _TAG_TO_CLASS


def test_school_can_be_placed_with_standard_2x2_rules() -> None:
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile()).level = 10
    cls = _TAG_TO_CLASS["SCHOOL"]
    assert cls.footprint == (2, 2)
    assert registry.can_place(cls, near_town_hall_tile(10, 10))
