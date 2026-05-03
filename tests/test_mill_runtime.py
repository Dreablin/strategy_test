"""Mill transport and worker-driven processing runtime."""

from __future__ import annotations

from game.buildings.base import Building
from game.buildings.mill import Mill
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.world import World
from game.workers import (
    Worker,
    WorkerManager,
    building_center_tile,
    mill_input_transport_tasks,
    mill_output_transport_tasks,
    processor_input_transport_tasks,
)


class WheatConsumer(Building):
    type_tag = "WHEAT_CONSUMER"
    __slots__ = ("active", "wheat_in")

    def __init__(self, level: int = 1, grid_pos: tuple[int, int] | None = None) -> None:
        super().__init__(level, grid_pos)
        self.active = True
        self.wheat_in = 0

    def input_capacity(self) -> int:
        return 2

    def input_amount(self) -> int:
        return self.wheat_in

    def add_wheat_in(self, amount: int) -> None:
        self.wheat_in += int(amount)


def test_mill_input_transport_tasks_generate_wheat_refill() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    mill = registry.place(Mill, near_town_hall_tile(12, 8))
    mill.construction_site = None
    mill.add_wheat_in(1)
    town_hall.add_to_warehouse("wheat", 2)

    tasks = mill_input_transport_tasks(registry)

    assert len(tasks) == 2
    assert all(t.resource == "wheat" for t in tasks)
    assert all(t.source is town_hall for t in tasks)
    assert all(t.target is mill for t in tasks)
    assert all(t.priority == 0 for t in tasks)


def test_wheat_input_transport_tasks_target_any_wheat_consumer() -> None:
    world = World(world_seed=0)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    consumer = registry.place(WheatConsumer, near_town_hall_tile(12, 8))
    town_hall.add_to_warehouse("wheat", 2)

    tasks = processor_input_transport_tasks(registry, "wheat")

    assert len(tasks) == 2
    assert all(t.resource == "wheat" for t in tasks)
    assert all(t.source is town_hall for t in tasks)
    assert all(t.target is consumer for t in tasks)


def test_mill_output_transport_tasks_generate_flour_exports() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    mill = registry.place(Mill, near_town_hall_tile(16, 8))
    mill.construction_site = None
    mill.add_flour_out(2)

    tasks = mill_output_transport_tasks(registry)

    assert len(tasks) == 2
    assert all(t.resource == "flour" for t in tasks)
    assert all(t.source is mill for t in tasks)
    assert all(t.target is town_hall for t in tasks)
    assert all(t.priority == 0 for t in tasks)


def test_mill_does_not_process_without_miller() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    mill = registry.place(Mill, near_town_hall_tile(16, 8))
    mill.construction_site = None
    mill.add_wheat_in(1)
    workers = WorkerManager(registry, now_ms_fn=lambda: 0)

    workers.update(1_000)
    assert mill.processing_started_ms == 0
    assert mill.input_amount() == 1
    assert mill.output_amount() == 0

    workers.update(31_000)
    assert mill.processing_started_ms == 0
    assert mill.input_amount() == 1
    assert mill.output_amount() == 0


def test_miller_processes_wheat_into_flour_and_rests() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    mill = registry.place(Mill, near_town_hall_tile(16, 8))
    mill.construction_site = None
    mill.add_wheat_in(1)
    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    miller = Worker("MILLER")
    workers.add_worker(miller)
    workers.assign_to_building(miller, mill)
    miller.current_tile = building_center_tile(mill)
    miller.stand_tile = miller.current_tile
    miller.state = "working"

    workers.update(1_000)
    assert miller.state == "processing"
    assert mill.processing_started_ms == 1_000

    workers.update(31_000)
    assert mill.input_amount() == 0
    assert mill.output_amount() == 1
    assert mill.processing_started_ms == 0
    assert miller.state == "resting"
    assert miller.camp_wait_until_ms == 41_000


def test_mill_inactive_mid_cycle_finishes_current_then_blocks_next() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    mill = registry.place(Mill, near_town_hall_tile(18, 8))
    mill.construction_site = None
    mill.add_wheat_in(2)
    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    miller = Worker("MILLER")
    workers.add_worker(miller)
    workers.assign_to_building(miller, mill)
    miller.current_tile = building_center_tile(mill)
    miller.stand_tile = miller.current_tile
    miller.state = "working"

    workers.update(1_000)
    assert mill.processing_started_ms == 1_000
    mill.set_active(False)

    workers.update(31_000)
    assert mill.input_amount() == 1
    assert mill.output_amount() == 1
    assert mill.processing_started_ms == 0

    assert miller.state == "resting"
    workers.update(42_000)
    assert mill.input_amount() == 1
    assert mill.output_amount() == 1
    assert mill.processing_started_ms == 0


def test_reassign_all_assigns_miller_only_to_mill() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    mill = registry.place(Mill, near_town_hall_tile(14, 8))
    mill.construction_site = None
    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    miller = Worker("MILLER")
    workers.add_worker(miller)

    workers.reassign_all()

    assert miller.assigned_building is mill


def test_mill_inactive_blocks_wheat_refill_tasks() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    mill = registry.place(Mill, near_town_hall_tile(20, 8))
    mill.construction_site = None
    mill.set_active(False)
    town_hall.add_to_warehouse("wheat", 3)

    assert mill_input_transport_tasks(registry) == []


def test_carrier_refills_mill_wheat_and_exports_flour() -> None:
    world = World(world_seed=2)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    mill = registry.place(Mill, near_town_hall_tile(18, 8))
    mill.construction_site = None
    town_hall.add_to_warehouse("wheat", 1)
    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    carrier = workers.hire("CARRIER")
    assert carrier is not None
    workers.enqueue_transport_task(resource="wheat", source=town_hall, target=mill, amount=1)

    for now_ms in range(0, 120_000, 500):
        workers.update(now_ms)
        if mill.input_amount() >= 1:
            break

    assert mill.input_amount() == 1
    assert town_hall.warehouse_amount("wheat") == 0

    mill.take_wheat_in(1)
    mill.add_flour_out(1)
    workers.enqueue_transport_task(resource="flour", source=mill, target=town_hall, amount=1)

    for now_ms in range(120_000, 300_000, 500):
        workers.update(now_ms)
        if town_hall.warehouse_amount("flour") >= 1:
            break

    assert town_hall.warehouse_amount("flour") == 1
    assert mill.output_amount() == 0
