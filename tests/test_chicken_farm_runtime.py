"""Chicken farm transport and worker-driven production runtime."""

from __future__ import annotations

from game.buildings.chicken_farm import ChickenFarm
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.buildings.well import Well
from game.config import building_level_int_setting, near_town_hall_tile, town_hall_origin_tile
from game.world import World
from game.workers import (
    Worker,
    WorkerManager,
    building_center_tile,
    chicken_farm_output_transport_tasks,
    processor_input_transport_tasks,
)


def test_chicken_farm_storage_capacity_uses_building_settings() -> None:
    for level in (1, 2, 3, 10):
        expected = building_level_int_setting("CHICKEN_FARM", "storage", level)
        assert ChickenFarm(level=level).input_capacity() == expected


def test_chicken_farm_input_transport_tasks_generate_wheat_refill() -> None:
    world = World(world_seed=0)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    world._iron.clear()  # noqa: SLF001
    world._gold.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    farm = registry.place(ChickenFarm, near_town_hall_tile(12, 8))
    farm.construction_site = None
    farm.add_wheat_in(1)
    town_hall.add_to_warehouse("wheat", 2)

    tasks = processor_input_transport_tasks(registry, "wheat")

    assert len(tasks) == 2
    assert all(t.resource == "wheat" for t in tasks)
    assert all(t.source is town_hall for t in tasks)
    assert all(t.target is farm for t in tasks)


def test_chicken_farm_output_transport_tasks_generate_chicken_exports() -> None:
    world = World(world_seed=0)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    world._iron.clear()  # noqa: SLF001
    world._gold.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    farm = registry.place(ChickenFarm, near_town_hall_tile(14, 8))
    farm.construction_site = None
    farm.add_chicken_out(2)

    tasks = chicken_farm_output_transport_tasks(registry)

    assert len(tasks) == 2
    assert all(t.resource == "chicken" for t in tasks)
    assert all(t.source is farm for t in tasks)
    assert all(t.target is town_hall for t in tasks)


def test_chicken_farm_requires_both_grain_and_water_to_start() -> None:
    world = World(world_seed=0)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    world._iron.clear()  # noqa: SLF001
    world._gold.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    farm = registry.place(ChickenFarm, near_town_hall_tile(18, 8))
    farm.construction_site = None
    farm.add_wheat_in(1)
    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    herder = Worker("ANIMAL_HERDER")
    workers.add_worker(herder)
    workers.assign_to_building(herder, farm)
    herder.current_tile = building_center_tile(farm)
    herder.stand_tile = herder.current_tile
    herder.state = "working"

    workers.update(1_000)

    assert herder.state == "working"
    assert farm.processing_started_ms == 0
    assert farm.output_amount() == 0


def test_animal_herder_processes_wheat_and_water_into_chicken_and_rests() -> None:
    world = World(world_seed=0)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    world._iron.clear()  # noqa: SLF001
    world._gold.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    farm = registry.place(ChickenFarm, near_town_hall_tile(18, 8))
    farm.construction_site = None
    farm.add_wheat_in(1)
    farm.add_water_in(1)
    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    herder = Worker("ANIMAL_HERDER")
    workers.add_worker(herder)
    workers.assign_to_building(herder, farm)
    herder.current_tile = building_center_tile(farm)
    herder.stand_tile = herder.current_tile
    herder.state = "working"

    workers.update(1_000)
    assert herder.state == "processing"
    assert farm.processing_started_ms == 1_000

    workers.update(46_000)
    assert farm.input_amount() == 0
    assert farm.water_amount() == 0
    assert farm.output_amount() == 1
    assert farm.processing_started_ms == 0
    assert herder.state == "resting"
    assert herder.camp_wait_until_ms == 56_000


def test_animal_herder_reassigns_only_to_chicken_farm() -> None:
    world = World(world_seed=0)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    world._iron.clear()  # noqa: SLF001
    world._gold.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    farm = registry.place(ChickenFarm, near_town_hall_tile(14, 8))
    farm.construction_site = None
    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    herder = Worker("ANIMAL_HERDER")
    workers.add_worker(herder)

    workers.reassign_all()

    assert herder.assigned_building is farm


def test_carrier_refills_chicken_farm_with_wheat_and_water() -> None:
    world = World(world_seed=2)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    world._iron.clear()  # noqa: SLF001
    world._gold.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    farm = registry.place(ChickenFarm, near_town_hall_tile(18, 8))
    well = registry.place(Well, near_town_hall_tile(24, 8))
    farm.construction_site = None
    well.construction_site = None
    town_hall.add_to_warehouse("wheat", 1)
    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    carrier = workers.hire("CARRIER")

    for now_ms in range(0, 180_000, 500):
        workers.update(now_ms)
        if farm.input_amount() >= 1 and farm.water_amount() >= 1:
            break

    assert farm.input_amount() == 1
    assert farm.water_amount() == 1
    assert town_hall.warehouse_amount("wheat") == 0
    assert well.busy is False
    assert carrier is not None


def test_carrier_exports_chicken_from_chicken_farm() -> None:
    world = World(world_seed=2)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    world._iron.clear()  # noqa: SLF001
    world._gold.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    farm = registry.place(ChickenFarm, near_town_hall_tile(18, 8))
    farm.construction_site = None
    farm.add_chicken_out(1)
    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    carrier = workers.hire("CARRIER")
    assert carrier is not None

    for now_ms in range(0, 220_000, 500):
        workers.update(now_ms)
        if town_hall.warehouse_amount("chicken") >= 1:
            break

    assert town_hall.warehouse_amount("chicken") == 1
    assert farm.output_amount() == 0
