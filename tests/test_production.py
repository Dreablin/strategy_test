"""Regression tests for staffed per-cycle income shown in Top Bar."""

from game.buildings.lumber_camp import LumberCamp
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.resources import ResourceManager
from game.world import World
from game.workers import WorkerManager


def test_per_cycle_counts_only_staffed_buildings() -> None:
    world = World()
    registry = BuildingRegistry(world)
    resources = ResourceManager()
    registry.place(TownHall, (16, 16))
    camp = registry.place(LumberCamp, (10, 10))
    wm = WorkerManager(resources, registry)
    assert wm.hire("LUMBERJACK") is not None
    wm.reassign_all()
    registry.sync_resources_per_cycle(resources, staffed_buildings=wm.staffed_buildings())
    assert wm.is_staffed(camp)
    assert resources.per_cycle["wood"] == 5


def test_per_cycle_updates_after_upgrade_for_staffed_building() -> None:
    world = World()
    registry = BuildingRegistry(world)
    resources = ResourceManager()
    registry.place(TownHall, (16, 16))
    camp = registry.place(LumberCamp, (10, 10))
    wm = WorkerManager(resources, registry)
    assert wm.hire("LUMBERJACK") is not None
    wm.reassign_all()
    registry.sync_resources_per_cycle(resources, staffed_buildings=wm.staffed_buildings())
    assert resources.per_cycle["wood"] == 5

    resources.add("wood", 500)
    assert registry.upgrade_building(camp, resources)
    registry.sync_resources_per_cycle(resources, staffed_buildings=wm.staffed_buildings())
    assert resources.per_cycle["wood"] == 10
