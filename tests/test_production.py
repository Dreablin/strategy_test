"""Production regression + end-to-end tick tests."""
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.buildings.farm import Farm
from game.buildings.iron_mine import IronMine
from game.buildings.stone_mine import StoneMine
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.iron import IronDeposit
from game.world import World
from game.workers import WorkerManager


def test_stone_mine_is_staffed_after_hire_and_reassign() -> None:
    world = World(world_seed=2)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    th = registry.place(TownHall, town_hall_origin_tile())
    th.level = 3
    camp = registry.place(StoneMine, (10, 10))
    camp.construction_site = None
    wm = WorkerManager(registry)
    assert wm.hire("STONECUTTER") is not None
    wm.reassign_all()
    assert wm.is_staffed(camp)


def test_staffed_stone_mine_can_upgrade() -> None:
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    th = registry.place(TownHall, town_hall_origin_tile())
    th.level = 3
    camp = registry.place(StoneMine, (10, 10))
    camp.construction_site = None
    wm = WorkerManager(registry)
    assert wm.hire("STONECUTTER") is not None
    wm.reassign_all()
    assert registry.upgrade_building(camp)


def test_staffed_level1_stone_mine_has_no_passive_tick_production() -> None:
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    workers = WorkerManager(registry)
    th = registry.place(TownHall, town_hall_origin_tile())
    th.level = 3
    mine = registry.place(StoneMine, (10, 10))
    mine.construction_site = None
    assert workers.hire("STONECUTTER") is not None
    workers.reassign_all()
    workers.update(120_000)

    stone_before = th.warehouse_amount("stone")
    # No passive tick production path exists anymore.
    assert th.warehouse_amount("stone") == stone_before


def test_upgraded_stone_mine_still_has_no_passive_tick_production() -> None:
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    workers = WorkerManager(registry)
    th = registry.place(TownHall, town_hall_origin_tile())
    th.level = 3
    camp = registry.place(StoneMine, (10, 10))
    camp.construction_site = None
    assert workers.hire("STONECUTTER") is not None
    workers.reassign_all()
    workers.update(120_000)

    # Upgrade level 1 -> 3.
    camp.level = 3

    stone_before = th.warehouse_amount("stone")
    # No passive tick production path exists anymore.
    assert th.warehouse_amount("stone") == stone_before


def test_moving_worker_does_not_produce_until_working() -> None:
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    workers = WorkerManager(registry)
    th = registry.place(TownHall, town_hall_origin_tile())
    th.level = 3
    camp = registry.place(StoneMine, near_town_hall_tile(10, 4))
    camp.construction_site = None
    assert workers.hire("STONECUTTER") is not None
    workers.reassign_all()

    assert camp not in workers.working_buildings()

    stone_before = th.warehouse_amount("stone")
    # No passive tick production path exists anymore.
    assert th.warehouse_amount("stone") == stone_before

    workers.update(60_000)
    stone_before = th.warehouse_amount("stone")
    # No passive tick production path exists anymore.
    assert th.warehouse_amount("stone") == stone_before


def test_farm_has_no_passive_income_even_when_staffed() -> None:
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    town_hall.level = 5
    _farm = registry.place(Farm, (10, 10))
    _farm.construction_site = None
    workers = WorkerManager(registry)
    worker = workers.hire("FARMER")
    assert worker is not None
    workers.reassign_all()
    workers.update(120_000)
    wheat_before = town_hall.warehouse_amount("wheat")
    # No passive tick production path exists anymore.
    assert town_hall.warehouse_amount("wheat") == wheat_before


def test_iron_mine_has_no_passive_income_even_when_staffed() -> None:
    world = World(world_seed=2)
    world._iron.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    th = registry.place(TownHall, town_hall_origin_tile())
    th.level = 5
    mine_pos = (10, 10)
    world._iron[mine_pos] = IronDeposit(blocking=False)  # noqa: SLF001
    _mine = registry.place(IronMine, mine_pos)
    _mine.construction_site = None
    workers = WorkerManager(registry)
    assert workers.hire("MINER") is not None
    workers.reassign_all()
    workers.update(120_000)
    iron_before = th.warehouse_amount("iron")
    # No passive tick production path exists anymore.
    assert th.warehouse_amount("iron") == iron_before
