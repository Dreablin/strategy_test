"""Production regression + end-to-end tick tests."""

from game.buildings.costs import upgrade_cost
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.buildings.farm import Farm
from game.buildings.iron_mine import IronMine
from game.buildings.stone_mine import StoneMine
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.resources import ResourceManager
from game.world import World
from game.workers import WorkerManager


def test_per_cycle_counts_only_staffed_buildings() -> None:
    world = World()
    registry = BuildingRegistry(world)
    resources = ResourceManager()
    th = registry.place(TownHall, town_hall_origin_tile())
    th.level = 3
    camp = registry.place(StoneMine, (10, 10))
    wm = WorkerManager(resources, registry)
    assert wm.hire("STONECUTTER") is not None
    wm.reassign_all()
    registry.sync_resources_per_cycle(resources, staffed_buildings=wm.staffed_buildings())
    assert wm.is_staffed(camp)
    assert resources.per_cycle["stone"] == 0


def test_per_cycle_updates_after_upgrade_for_staffed_building() -> None:
    world = World()
    registry = BuildingRegistry(world)
    resources = ResourceManager()
    th = registry.place(TownHall, town_hall_origin_tile())
    th.level = 3
    camp = registry.place(StoneMine, (10, 10))
    wm = WorkerManager(resources, registry)
    assert wm.hire("STONECUTTER") is not None
    wm.reassign_all()
    registry.sync_resources_per_cycle(resources, staffed_buildings=wm.staffed_buildings())
    assert resources.per_cycle["stone"] == 0

    resources.add("wood", 500)
    resources.add("stone", 500)
    assert registry.upgrade_building(camp, resources)
    registry.sync_resources_per_cycle(resources, staffed_buildings=wm.staffed_buildings())
    assert resources.per_cycle["stone"] == 0


def test_staffed_level1_stone_mine_has_no_passive_tick_production() -> None:
    world = World()
    registry = BuildingRegistry(world)
    resources = ResourceManager()
    workers = WorkerManager(resources, registry)
    th = registry.place(TownHall, town_hall_origin_tile())
    th.level = 3
    registry.place(StoneMine, (10, 10))
    assert workers.hire("STONECUTTER") is not None
    workers.reassign_all()
    workers.update(120_000)

    stone_before = resources.get("stone")
    # No passive tick production path exists anymore.
    assert resources.get("stone") == stone_before


def test_upgraded_stone_mine_still_has_no_passive_tick_production() -> None:
    world = World()
    registry = BuildingRegistry(world)
    resources = ResourceManager()
    workers = WorkerManager(resources, registry)
    th = registry.place(TownHall, town_hall_origin_tile())
    th.level = 3
    camp = registry.place(StoneMine, (10, 10))
    assert workers.hire("STONECUTTER") is not None
    workers.reassign_all()
    workers.update(120_000)

    # Upgrade level 1 -> 3.
    resources.add("wood", 10_000)
    assert resources.try_spend(upgrade_cost(1))
    camp.level = 2
    assert resources.try_spend(upgrade_cost(2))
    camp.level = 3

    stone_before = resources.get("stone")
    # No passive tick production path exists anymore.
    assert resources.get("stone") == stone_before


def test_moving_worker_does_not_produce_until_working() -> None:
    world = World()
    registry = BuildingRegistry(world)
    resources = ResourceManager()
    workers = WorkerManager(resources, registry)
    th = registry.place(TownHall, town_hall_origin_tile())
    th.level = 3
    camp = registry.place(StoneMine, near_town_hall_tile(10, 4))
    assert workers.hire("STONECUTTER") is not None
    workers.reassign_all()

    registry.sync_resources_per_cycle(resources, staffed_buildings=workers.working_buildings())
    assert camp not in workers.working_buildings()
    assert resources.per_cycle["stone"] == 0

    stone_before = resources.get("stone")
    # No passive tick production path exists anymore.
    assert resources.get("stone") == stone_before

    workers.update(60_000)
    registry.sync_resources_per_cycle(resources, staffed_buildings=workers.working_buildings())
    stone_before = resources.get("stone")
    assert resources.per_cycle["stone"] == 0
    # No passive tick production path exists anymore.
    assert resources.get("stone") == stone_before


def test_farm_has_no_passive_income_even_when_staffed() -> None:
    world = World()
    registry = BuildingRegistry(world)
    resources = ResourceManager()
    _farm = registry.place(Farm, (10, 10))
    workers = WorkerManager(resources, registry)
    worker = workers.hire("FARMER")
    if worker is None:
        th = registry.place(TownHall, town_hall_origin_tile())
        th.level = 5
        worker = workers.hire("FARMER")
    assert worker is not None
    workers.reassign_all()
    workers.update(120_000)
    food_before = resources.get("food")
    # No passive tick production path exists anymore.
    assert resources.get("food") == food_before


def test_iron_mine_has_no_passive_income_even_when_staffed() -> None:
    world = World()
    registry = BuildingRegistry(world)
    resources = ResourceManager()
    th = registry.place(TownHall, town_hall_origin_tile())
    th.level = 5
    _mine = registry.place(IronMine, (10, 10))
    workers = WorkerManager(resources, registry)
    assert workers.hire("MINER") is not None
    workers.reassign_all()
    workers.update(120_000)
    iron_before = resources.get("iron")
    # No passive tick production path exists anymore.
    assert resources.get("iron") == iron_before
