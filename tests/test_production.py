"""Production regression + end-to-end tick tests."""

from game.buildings.costs import upgrade_cost
from game.buildings.lumber_camp import LumberCamp
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.config import TICK_MS
from game.resources import ResourceManager
from game.tick import TickScheduler
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


def _apply_production_tick(registry: BuildingRegistry, resources: ResourceManager, workers: WorkerManager) -> None:
    """T38 target API: apply one production cycle from staffed buildings."""
    from game.loop import apply_production_tick

    apply_production_tick(registry, resources, workers)


def test_tick_adds_5_wood_for_staffed_level1_lumber_camp() -> None:
    world = World()
    registry = BuildingRegistry(world)
    resources = ResourceManager()
    workers = WorkerManager(resources, registry)
    scheduler = TickScheduler()
    registry.place(TownHall, (16, 16))
    registry.place(LumberCamp, (10, 10))
    assert workers.hire("LUMBERJACK") is not None
    workers.reassign_all()
    workers.update(120_000)

    wood_before = resources.get("wood")
    assert scheduler.update(TICK_MS) is True
    _apply_production_tick(registry, resources, workers)
    assert resources.get("wood") == wood_before + 5


def test_tick_after_upgrade_to_level3_adds_15_wood() -> None:
    world = World()
    registry = BuildingRegistry(world)
    resources = ResourceManager()
    workers = WorkerManager(resources, registry)
    scheduler = TickScheduler()
    registry.place(TownHall, (16, 16))
    camp = registry.place(LumberCamp, (10, 10))
    assert workers.hire("LUMBERJACK") is not None
    workers.reassign_all()
    workers.update(120_000)

    # Upgrade level 1 -> 3.
    resources.add("wood", 10_000)
    assert resources.try_spend(upgrade_cost(1))
    camp.level = 2
    assert resources.try_spend(upgrade_cost(2))
    camp.level = 3

    wood_before = resources.get("wood")
    assert scheduler.update(TICK_MS) is True
    _apply_production_tick(registry, resources, workers)
    assert resources.get("wood") == wood_before + 15


def test_moving_worker_does_not_produce_until_working() -> None:
    world = World()
    registry = BuildingRegistry(world)
    resources = ResourceManager()
    workers = WorkerManager(resources, registry)
    registry.place(TownHall, (16, 16))
    camp = registry.place(LumberCamp, (24, 24))
    assert workers.hire("LUMBERJACK") is not None
    workers.reassign_all()

    registry.sync_resources_per_cycle(resources, staffed_buildings=workers.working_buildings())
    assert camp not in workers.working_buildings()
    assert resources.per_cycle["wood"] == 0

    wood_before = resources.get("wood")
    _apply_production_tick(registry, resources, workers)
    assert resources.get("wood") == wood_before

    workers.update(60_000)
    registry.sync_resources_per_cycle(resources, staffed_buildings=workers.working_buildings())
    wood_before = resources.get("wood")
    assert resources.per_cycle["wood"] == 5
    _apply_production_tick(registry, resources, workers)
    assert resources.get("wood") == wood_before + 5
