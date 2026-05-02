"""School building registration and placement."""

from game.ui.placement import _TAG_TO_CLASS
from game.world import World
from game.buildings.registry import BuildingRegistry
from game.buildings.school import School
from game.buildings.town_hall import TownHall
from game.config import CONSTRUCTION_REQUIREMENTS, town_hall_origin_tile, near_town_hall_tile


def test_school_registered_in_placement_tags() -> None:
    assert "SCHOOL" in _TAG_TO_CLASS


def test_school_can_be_placed_with_standard_2x2_rules() -> None:
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile()).level = 10
    cls = _TAG_TO_CLASS["SCHOOL"]
    assert cls.footprint == (2, 2)
    assert registry.can_place(cls, near_town_hall_tile(10, 10))


def test_school_supports_standard_ten_levels() -> None:
    school = School(level=10)

    assert school.level == 10
    assert School.max_level() == 10


def test_upgrade_school_starts_construction_for_level2() -> None:
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile()).level = 10
    school = registry.place(School, near_town_hall_tile(10, 10))
    school.construction_site = None

    assert registry.upgrade_building(school)
    assert school.level == 1
    assert school.is_under_construction
    assert school.construction_site is not None
    assert school.construction_site.target_level == 2
    assert school.construction_site.required_resources == CONSTRUCTION_REQUIREMENTS["SCHOOL"][2].cost
