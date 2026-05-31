"""Bakery transport and worker-driven bread production."""

from __future__ import annotations

from game.buildings.bakery import Bakery
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.buildings.well import Well
from game.config import building_level_int_setting, near_town_hall_tile, town_hall_origin_tile
from game.world import World
from game.workers import (
    Worker,
    WorkerManager,
    bakery_input_transport_tasks,
    bakery_output_transport_tasks,
    building_center_tile,
    mill_output_transport_tasks,
    water_input_transport_tasks,
)


def test_bakery_storage_capacity_uses_building_settings() -> None:
    for level in (1, 2, 3, 10):
        assert Bakery(level=level).input_capacity() == building_level_int_setting("BAKERY", "storage", level)


def test_bakery_input_transport_tasks_generate_flour_refill() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    bakery = registry.place(Bakery, near_town_hall_tile(12, 8))
    bakery.construction_site = None
    bakery.add_flour_in(1)
    town_hall.add_to_warehouse("flour", 3)

    tasks = bakery_input_transport_tasks(registry)

    assert len(tasks) == 2
    assert all(t.resource == "flour" for t in tasks)
    assert all(t.source is town_hall for t in tasks)
    assert all(t.target is bakery for t in tasks)


def test_bakery_output_transport_tasks_generate_bread_exports() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    bakery = registry.place(Bakery, near_town_hall_tile(14, 8))
    bakery.construction_site = None
    bakery.add_bread_out(2)

    tasks = bakery_output_transport_tasks(registry)

    assert len(tasks) == 2
    assert all(t.resource == "bread" for t in tasks)
    assert all(t.source is bakery for t in tasks)
    assert all(t.target is town_hall for t in tasks)


def test_water_input_transport_tasks_require_stored_well_water() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    bakery = registry.place(Bakery, near_town_hall_tile(14, 8))
    well = registry.place(Well, near_town_hall_tile(20, 8))
    bakery.construction_site = None
    well.construction_site = None

    assert water_input_transport_tasks(registry) == []

    well.add_water_in(1)
    tasks = water_input_transport_tasks(registry)

    assert len(tasks) == 1
    assert tasks[0].resource == "water"
    assert tasks[0].source is well
    assert tasks[0].target is bakery


def test_water_input_transport_tasks_respect_pending_well_pickups() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    bakery = registry.place(Bakery, near_town_hall_tile(14, 8))
    well = registry.place(Well, near_town_hall_tile(20, 8))
    bakery.construction_site = None
    well.construction_site = None
    well.add_water_in(1)

    pending = {id(well): 1}
    assert water_input_transport_tasks(registry, pending_pickups_by_well_id=pending) == []


def test_water_input_transport_tasks_support_any_water_consumer() -> None:
    class WaterConsumer:
        type_tag = "TEST_WATER_CONSUMER"
        grid_pos = near_town_hall_tile(16, 8)
        is_under_construction = False
        active = True

        def __init__(self) -> None:
            self.water = 1

        def water_amount(self) -> int:
            return self.water

        def water_capacity(self) -> int:
            return 3

        def add_water_in(self, amount: int) -> None:
            self.water += int(amount)

    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    well = registry.place(Well, near_town_hall_tile(20, 8))
    well.construction_site = None
    well.add_water_in(1)
    consumer = WaterConsumer()
    registry._buildings.append(consumer)  # noqa: SLF001

    tasks = water_input_transport_tasks(registry)

    assert len(tasks) == 1
    assert tasks[0].resource == "water"
    assert tasks[0].source is well
    assert tasks[0].target is consumer


def test_baker_processes_flour_and_water_into_bread_and_rests() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    bakery = registry.place(Bakery, near_town_hall_tile(16, 8))
    bakery.construction_site = None
    bakery.add_flour_in(1)
    bakery.add_water_in(1)
    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    baker = Worker("BAKER")
    workers.add_worker(baker)
    workers.assign_to_building(baker, bakery)
    baker.current_tile = building_center_tile(bakery)
    baker.stand_tile = baker.current_tile
    baker.state = "working"

    workers.update(1_000)
    assert baker.state == "processing"
    assert bakery.processing_started_ms == 1_000

    done_ms = bakery.processing_started_ms + bakery.processing_duration_ms
    workers.update(done_ms)
    assert bakery.input_amount() == 0
    assert bakery.water_amount() == 0
    assert bakery.output_amount() == 1
    assert bakery.processing_started_ms == 0
    assert baker.state == "resting"
    assert baker.camp_wait_until_ms > done_ms


def test_carrier_delivers_stored_water_from_well_to_bakery() -> None:
    world = World(world_seed=2)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    bakery = registry.place(Bakery, near_town_hall_tile(18, 8))
    well = registry.place(Well, near_town_hall_tile(24, 8))
    bakery.construction_site = None
    well.construction_site = None
    well.add_water_in(1)
    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    carrier = workers.hire("CARRIER")
    assert carrier is not None

    workers.update(0)

    for now_ms in range(500, 180_000, 500):
        workers.update(now_ms)
        if bakery.water_amount() >= 1:
            break

    assert bakery.water_amount() == 1
    assert town_hall.warehouse_amount("water") == 0


def test_well_reports_generic_storage_and_production_status() -> None:
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    well = registry.place(Well, near_town_hall_tile(24, 8))
    well.construction_site = None
    well.processing_started_ms = 5_000
    well.processing_duration_ms = 10_000
    workers = WorkerManager(registry, now_ms_fn=lambda: 10_000)
    waterman = Worker("WATERMAN")
    waterman.assigned_building = well
    waterman.state = "processing"
    workers.add_worker(waterman)

    assert workers.worker_status_for_building(well) == "assigned"
    assert workers.production_status_for_building(well) == "processing"
    assert well.processing_progress(10_000) == 0.5


def test_second_carrier_can_take_water_from_well_while_first_carries_to_bakery() -> None:
    world = World(world_seed=2)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    bakery = registry.place(Bakery, near_town_hall_tile(18, 8))
    well = registry.place(Well, near_town_hall_tile(24, 8))
    bakery.construction_site = None
    well.construction_site = None
    well.level = 5
    well.stored = 0
    well.add_water_in(5)
    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    first = workers.hire("CARRIER")
    second = workers.hire("CARRIER")
    assert first is not None
    assert second is not None

    workers.update(0)

    for now_ms in range(500, 120_000, 500):
        workers.update(now_ms)
        if first.carrying == "water" and first.state == "moving":
            break

    assert first.carrying == "water"
    assert workers.worker_status_for_building(well) == "empty"
    assert workers.production_status_for_building(well) == "no_worker"

    workers.update(now_ms + 500)

    assert second.transport_task is not None
    assert second.transport_task.resource == "water"
    assert second.transport_task.source is well


def test_bakery_requires_both_flour_and_water_to_start() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    bakery = registry.place(Bakery, near_town_hall_tile(18, 8))
    bakery.construction_site = None
    bakery.add_flour_in(1)
    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    baker = Worker("BAKER")
    workers.add_worker(baker)
    workers.assign_to_building(baker, bakery)
    baker.current_tile = building_center_tile(bakery)
    baker.stand_tile = baker.current_tile
    baker.state = "working"

    workers.update(1_000)

    assert baker.state == "working"
    assert bakery.processing_started_ms == 0
    assert bakery.output_amount() == 0


def test_reassign_all_assigns_baker_only_to_bakery() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    bakery = registry.place(Bakery, near_town_hall_tile(14, 8))
    bakery.construction_site = None
    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    baker = Worker("BAKER")
    workers.add_worker(baker)

    workers.reassign_all()

    assert baker.assigned_building is bakery


def test_mill_flour_output_can_target_bakery_before_town_hall() -> None:
    from game.buildings.mill import Mill

    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    mill = registry.place(Mill, near_town_hall_tile(12, 8))
    bakery = registry.place(Bakery, near_town_hall_tile(20, 8))
    mill.construction_site = None
    bakery.construction_site = None
    mill.add_flour_out(1)

    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    for task in mill_output_transport_tasks(registry):
        target = workers._processor_input_target_for_resource(task.resource, source=task.source)  # noqa: SLF001
        assert target is bakery
