"""SCIENTIST hire metadata tests (T399)."""

from __future__ import annotations

from game import config
from game.buildings.registry import BuildingRegistry
from game.buildings.school import School
from game.buildings.town_hall import TownHall
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.worker_hiring import HIRABLE_WORKERS, WORKER_TO_BUILDING
from game.worker_tiers import worker_tier, workers_of_tier
from game.workers import WorkerManager
from game.world import World


def test_scientist_tier_is_advanced_in_settings() -> None:
    assert config.SETTINGS["workers"]["tiers"]["SCIENTIST"] == "advanced"
    assert worker_tier("SCIENTIST") == "advanced"
    assert "SCIENTIST" in workers_of_tier("advanced")


def test_scientist_has_hire_gate_in_settings() -> None:
    assert config.SETTINGS["gates"]["hire_min_town_hall_level"]["SCIENTIST"] == 1
    assert config.TOWN_HALL_MIN_LEVEL_FOR_HIRE["SCIENTIST"] == 1


def test_scientist_is_hirable_without_building_assignment_mapping() -> None:
    assert "SCIENTIST" in HIRABLE_WORKERS
    assert "SCIENTIST" not in WORKER_TO_BUILDING


def test_scientist_can_be_hired_from_school() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    town_hall.construction_site = None
    school = registry.place(School, near_town_hall_tile(8, 8))
    school.construction_site = None
    workers = WorkerManager(registry)
    scientist = workers.hire("SCIENTIST", source_building=school)
    assert scientist is not None
    assert scientist.type_tag == "SCIENTIST"
