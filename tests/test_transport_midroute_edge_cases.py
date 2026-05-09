"""RED tests for transport mid-route edge cases (T239)."""

from __future__ import annotations

from game.construction import ConstructionSite
from game.buildings.bakery import Bakery
from game.buildings.chicken_farm import ChickenFarm
from game.buildings.farm import Farm
from game.buildings.lumber_camp import LumberCamp
from game.buildings.mill import Mill
from game.buildings.registry import BuildingRegistry
from game.buildings.sawmill import Sawmill
from game.buildings.town_hall import TownHall
from game.buildings.well import Well
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.world import World
from game.workers import TransportTask, Worker, WorkerManager, building_center_tile


def _advance_until_loading(workers: WorkerManager, carrier, *, max_steps: int = 200, step_ms: int = 500) -> None:
    now_ms = 0
    for _ in range(max_steps):
        workers.update(now_ms)
        if carrier.state == "carrier_loading":
            return
        now_ms += step_ms
    raise AssertionError("carrier never reached loading state")


def _empty_world() -> World:
    world = World(world_seed=9)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    world._iron.clear()  # noqa: SLF001
    world._gold.clear()  # noqa: SLF001
    return world


def _advance_until_idle_without_task(
    workers: WorkerManager,
    carrier,
    *,
    start_ms: int = 0,
    max_steps: int = 200,
    step_ms: int = 1_000,
) -> None:
    now_ms = start_ms
    for _ in range(max_steps):
        workers.update(now_ms)
        if carrier.transport_task is None and carrier.carrying is None and carrier.state == "idle":
            return
        now_ms += step_ms
    raise AssertionError("carrier did not finish cancelled delivery")


def test_stale_farm_wheat_task_is_dropped_when_source_empty_mid_route() -> None:
    world = _empty_world()
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    farm = registry.place(Farm, near_town_hall_tile(10, 8))
    farm.construction_site = None
    farm.stored = 1

    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    carrier = workers.hire("CARRIER")
    assert carrier is not None

    workers.enqueue_transport_task(resource="wheat", source=farm, target=town_hall, amount=1, priority=0)
    _advance_until_loading(workers, carrier)

    # Mid-route source mutation: wheat already removed elsewhere.
    farm.stored = 0
    carrier.camp_wait_until_ms = 0
    workers.update(5_000)

    # Expect stale task to be removed, not left to clog queue retries.
    assert carrier.transport_task is None
    assert carrier.state == "idle"
    assert not any(
        t.resource == "wheat" and t.source is farm and t.target is town_hall
        for t in workers._transport_queue  # noqa: SLF001
    )


def test_carrier_returns_resource_to_town_hall_when_construction_target_is_demolished() -> None:
    world = _empty_world()
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    target = registry.place(Sawmill, near_town_hall_tile(10, 8))

    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    carrier = workers.hire("CARRIER")
    assert carrier is not None
    carrier.current_tile = near_town_hall_tile(6, 8)
    carrier.stand_tile = carrier.current_tile
    carrier.state = "moving"
    carrier.transport_task = TransportTask("wood", town_hall, target, priority=10, purpose="construction")
    carrier.carrying = "wood"

    registry.demolish(target, workers)
    workers.update(0)

    assert carrier.transport_task is not None
    assert carrier.transport_task.returning_to_town_hall
    assert carrier.transport_task.target is town_hall

    _advance_until_idle_without_task(workers, carrier, start_ms=1_000)

    assert town_hall.warehouse_amount("wood") == 1
    assert target not in registry.all()


def test_water_delivery_is_dropped_when_processor_target_starts_upgrade() -> None:
    world = _empty_world()
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    town_hall.construction_site = None
    town_hall.add_to_warehouse("boards", 3)
    town_hall.add_to_warehouse("stone", 1)
    target = registry.place(ChickenFarm, near_town_hall_tile(18, 8))
    target.construction_site = None
    well = registry.place(Well, near_town_hall_tile(24, 8))
    well.construction_site = None

    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    registry.bind_worker_manager(workers)
    carrier = Worker("CARRIER")
    workers.add_worker(carrier)
    carrier.transport_task = TransportTask("water", well, target)
    carrier.carrying = "water"
    carrier.state = "carrier_unloading"
    carrier.camp_wait_until_ms = 0

    assert registry.upgrade_building(target)

    workers.update(1_000)

    assert carrier.transport_task is None
    assert carrier.carrying is None
    assert carrier.state == "idle"
    assert town_hall.warehouse_amount("water") == 0


def test_queued_processor_delivery_is_removed_when_target_starts_upgrade() -> None:
    world = _empty_world()
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    town_hall.construction_site = None
    town_hall.add_to_warehouse("wheat", 1)
    town_hall.add_to_warehouse("boards", 3)
    town_hall.add_to_warehouse("stone", 1)
    target = registry.place(ChickenFarm, near_town_hall_tile(18, 8))
    target.construction_site = None

    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    registry.bind_worker_manager(workers)
    carrier = Worker("CARRIER")
    workers.add_worker(carrier)
    workers.enqueue_transport_task(resource="wheat", source=town_hall, target=target, amount=1)

    assert registry.upgrade_building(target)

    workers.update(1_000)

    active = [carrier.transport_task] if carrier.transport_task is not None else []
    queued_and_active = workers._transport_queue + active  # noqa: SLF001
    assert not any(t.resource == "wheat" and t.target is target for t in queued_and_active)
    assert target.input_amount() == 0
    assert town_hall.warehouse_amount("wheat") == 1


def test_carrier_returns_resource_when_construction_finishes_before_delivery_from_local_source() -> None:
    world = _empty_world()
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    source = registry.place(LumberCamp, near_town_hall_tile(8, 8))
    source.construction_site = None
    target = registry.place(Sawmill, near_town_hall_tile(14, 8))
    target.construction_site = ConstructionSite(
        required_resources={"wood": 1},
        delivered_resources={},
        build_time_ms=10_000,
        build_started_ms=None,
        builder=None,
        target_level=1,
    )

    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    carrier = workers.hire("CARRIER")
    assert carrier is not None
    carrier.current_tile = near_town_hall_tile(10, 8)
    carrier.stand_tile = carrier.current_tile
    carrier.state = "moving"
    carrier.transport_task = TransportTask(
        "wood",
        source,
        target,
        priority=10,
        purpose="construction",
    )
    carrier.carrying = "wood"

    target.construction_site = None
    workers.update(0)

    assert carrier.transport_task is not None
    assert carrier.transport_task.returning_to_town_hall
    assert carrier.transport_task.target is town_hall

    _advance_until_idle_without_task(workers, carrier, start_ms=1_000)

    assert town_hall.warehouse_amount("wood") == 1
    assert target.construction_site is None


def test_carrier_returns_resource_to_town_hall_when_processor_target_is_demolished() -> None:
    world = _empty_world()
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    target = registry.place(Bakery, near_town_hall_tile(10, 8))
    target.construction_site = None

    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    carrier = workers.hire("CARRIER")
    assert carrier is not None
    carrier.current_tile = near_town_hall_tile(6, 8)
    carrier.stand_tile = carrier.current_tile
    carrier.state = "moving"
    carrier.transport_task = TransportTask("flour", town_hall, target, priority=0)
    carrier.carrying = "flour"

    registry.demolish(target, workers)
    workers.update(0)
    _advance_until_idle_without_task(workers, carrier, start_ms=1_000)

    assert town_hall.warehouse_amount("flour") == 1
    assert target not in registry.all()


def test_carrier_drops_water_when_target_is_demolished() -> None:
    world = _empty_world()
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    well = registry.place(Well, near_town_hall_tile(6, 8))
    well.construction_site = None
    target = registry.place(Bakery, near_town_hall_tile(10, 8))
    target.construction_site = None

    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    carrier = workers.hire("CARRIER")
    assert carrier is not None
    carrier.current_tile = near_town_hall_tile(7, 8)
    carrier.stand_tile = carrier.current_tile
    carrier.state = "moving"
    carrier.transport_task = TransportTask("water", well, target, priority=0)
    carrier.carrying = "water"

    registry.demolish(target, workers)
    workers.update(0)

    assert carrier.transport_task is None
    assert carrier.carrying is None
    assert carrier.state == "idle"
    assert target not in registry.all()
    assert town_hall.warehouse_amount("water") == 0


def test_carrier_drops_water_when_source_well_demolished_mid_route() -> None:
    world = _empty_world()
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    well = registry.place(Well, near_town_hall_tile(6, 8))
    well.construction_site = None
    target = registry.place(Bakery, near_town_hall_tile(10, 8))
    target.construction_site = None

    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    carrier = workers.hire("CARRIER")
    assert carrier is not None
    carrier.current_tile = near_town_hall_tile(7, 8)
    carrier.stand_tile = carrier.current_tile
    carrier.state = "moving"
    carrier.transport_task = TransportTask("water", well, target, priority=0)
    carrier.carrying = "water"

    registry.demolish(well, workers)
    workers.update(0)

    assert carrier.transport_task is None
    assert carrier.carrying is None
    assert carrier.state == "idle"
    assert well not in registry.all()
    assert town_hall.warehouse_amount("water") == 0


def test_queued_water_transport_removed_when_well_demolished() -> None:
    world = _empty_world()
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    well = registry.place(Well, near_town_hall_tile(6, 8))
    well.construction_site = None
    well.add_water_in(1)
    bakery = registry.place(Bakery, near_town_hall_tile(10, 8))
    bakery.construction_site = None

    workers = WorkerManager(registry)
    workers.enqueue_transport_task(resource="water", source=well, target=bakery, amount=1)
    assert len(workers._transport_queue) == 1  # noqa: SLF001

    registry.demolish(well, workers)

    assert workers._transport_queue == []  # noqa: SLF001


def test_queued_transport_task_is_dropped_when_target_was_demolished() -> None:
    world = _empty_world()
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    target = registry.place(Sawmill, near_town_hall_tile(10, 8))
    target.construction_site = None
    town_hall.add_to_warehouse("wood", 1)

    workers = WorkerManager(registry)
    workers.enqueue_transport_task(resource="wood", source=town_hall, target=target, amount=1)

    registry.demolish(target, workers)

    assert workers._next_transport_task() is None  # noqa: SLF001
    assert workers._transport_queue == []  # noqa: SLF001


def test_active_transport_task_counts_against_processor_input_capacity() -> None:
    world = _empty_world()
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    mill = registry.place(Mill, near_town_hall_tile(10, 8))
    mill.construction_site = None
    town_hall.add_to_warehouse("wheat", 3)

    workers = WorkerManager(registry)
    carrier = Worker("CARRIER")
    carrier.transport_task = TransportTask("wheat", town_hall, mill)
    workers.add_worker(carrier)

    workers.update(0)
    workers.update(1_000)

    queued_wheat = [
        task
        for task in workers._transport_queue  # noqa: SLF001
        if task.resource == "wheat" and task.target is mill
    ]
    assert len(queued_wheat) == mill.input_capacity() - 1
    assert mill.input_amount() == 0


def test_active_transport_task_counts_against_construction_remaining_need() -> None:
    world = _empty_world()
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    target = registry.place(Sawmill, near_town_hall_tile(10, 8))
    site = target.construction_site
    assert site is not None
    site.required_resources = {"wood": 2}
    site.delivered_resources = {}
    town_hall.add_to_warehouse("wood", 2)

    workers = WorkerManager(registry)
    carrier = Worker("CARRIER")
    carrier.transport_task = TransportTask("wood", town_hall, target, priority=10, purpose="construction")
    workers.add_worker(carrier)

    workers.update(0)
    workers.update(1_000)

    queued_wood = [
        task
        for task in workers._transport_queue  # noqa: SLF001
        if task.resource == "wood" and task.target is target
    ]
    assert len(queued_wood) == 1


def test_carrier_cancelled_while_loading_construction_resource_exits_town_hall() -> None:
    world = _empty_world()
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    target = registry.place(Sawmill, near_town_hall_tile(10, 8))
    site = target.construction_site
    assert site is not None
    site.required_resources = {"wood": 1}
    site.delivered_resources = {}
    town_hall.add_to_warehouse("wood", 1)

    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    carrier = workers.hire("CARRIER")
    assert carrier is not None

    _advance_until_loading(workers, carrier)
    assert carrier.transport_task is not None
    assert carrier.current_tile == building_center_tile(town_hall)

    site.delivered_resources = {"wood": 1}
    workers.update(1_000)

    assert carrier.transport_task is None
    assert carrier.state == "idle"
    assert carrier.current_tile in workers._approach_tiles(town_hall)  # noqa: SLF001

    site.delivered_resources = {}
    workers.update(2_000)

    assert carrier.transport_task is not None
    assert carrier.state in {"moving", "working"}

    workers.update(2_500)

    assert carrier.state == "carrier_loading"


def test_carrier_exits_town_hall_when_warehouse_resource_is_unavailable_at_pickup() -> None:
    world = _empty_world()
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    target = registry.place(Sawmill, near_town_hall_tile(10, 8))
    site = target.construction_site
    assert site is not None
    site.required_resources = {"stone": 1}
    site.delivered_resources = {}

    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    carrier = workers.hire("CARRIER")
    assert carrier is not None
    carrier.current_tile = building_center_tile(town_hall)
    carrier.stand_tile = carrier.current_tile
    carrier.state = "carrier_loading"
    carrier.camp_wait_until_ms = 0
    carrier.transport_task = TransportTask("stone", town_hall, target, priority=10, purpose="construction")

    workers.update(0)

    assert carrier.transport_task is None
    assert carrier.carrying is None
    assert carrier.state == "idle"
    assert carrier.current_tile in workers._approach_tiles(town_hall)  # noqa: SLF001
    assert any(
        task.resource == "stone" and task.source is town_hall and task.target is target
        for task in workers._transport_queue  # noqa: SLF001
    )

    town_hall.add_to_warehouse("stone", 1)
    for now_ms in range(1_000, 120_000, 500):
        workers.update(now_ms)
        if site.delivered_resources.get("stone", 0) >= 1:
            break

    assert site.delivered_resources.get("stone", 0) == 1
    assert carrier.current_tile != building_center_tile(town_hall)


def test_carrier_returns_resource_to_town_hall_when_source_is_demolished_after_pickup() -> None:
    world = _empty_world()
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    source = registry.place(Sawmill, near_town_hall_tile(10, 8))
    source.construction_site = None
    source.add_boards_out(1)

    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    carrier = workers.hire("CARRIER")
    assert carrier is not None
    carrier.current_tile = near_town_hall_tile(12, 8)
    carrier.stand_tile = carrier.current_tile
    carrier.state = "moving"
    carrier.transport_task = TransportTask("boards", source, town_hall)
    carrier.carrying = "boards"

    registry.demolish(source, workers)
    workers.update(0)
    _advance_until_idle_without_task(workers, carrier, start_ms=1_000)

    assert town_hall.warehouse_amount("boards") == 1
    assert source not in registry.all()


def test_water_task_clears_carrier_when_target_demolished_before_pickup() -> None:
    world = _empty_world()
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    well = registry.place(Well, near_town_hall_tile(6, 8))
    well.construction_site = None
    well.add_water_in(1)
    target = registry.place(Bakery, near_town_hall_tile(10, 8))
    target.construction_site = None

    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    carrier = workers.hire("CARRIER")
    assert carrier is not None
    carrier.transport_task = TransportTask("water", well, target)
    carrier.state = "carrier_loading"
    carrier.camp_wait_until_ms = 10_000

    registry.demolish(target, workers)
    workers.update(0)

    assert carrier.transport_task is None
    assert carrier.carrying is None
    assert carrier.state == "idle"
    assert town_hall.warehouse_amount("water") == 0


def test_empty_well_water_task_does_not_block_other_available_tasks() -> None:
    world = _empty_world()
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    town_hall.add_to_warehouse("wood", 1)
    well = registry.place(Well, near_town_hall_tile(6, 8))
    well.construction_site = None
    bakery = registry.place(Bakery, near_town_hall_tile(10, 8))
    bakery.construction_site = None
    sawmill = registry.place(Sawmill, near_town_hall_tile(14, 8))
    sawmill.construction_site = None

    workers = WorkerManager(registry)
    workers.enqueue_transport_task(resource="water", source=well, target=bakery, amount=1)
    workers.enqueue_transport_task(resource="wood", source=town_hall, target=sawmill, amount=1)

    picked = workers._next_transport_task()  # noqa: SLF001

    assert picked is not None
    assert picked.resource == "wood"
    assert picked.target is sawmill
    assert any(
        task.resource == "water" and task.source is well and task.target is bakery
        for task in workers._transport_queue  # noqa: SLF001
    )


def test_water_inbound_tasks_count_against_target_capacity() -> None:
    world = _empty_world()
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    well_a = registry.place(Well, near_town_hall_tile(4, 4))
    well_b = registry.place(Well, near_town_hall_tile(7, 4))
    well_c = registry.place(Well, near_town_hall_tile(10, 4))
    for well in (well_a, well_b, well_c):
        well.construction_site = None
        well.add_water_in(1)
    bakery = registry.place(Bakery, near_town_hall_tile(12, 8))
    bakery.construction_site = None
    bakery.add_water_in(bakery.water_capacity() - 2)

    workers = WorkerManager(registry)
    carrier = Worker("CARRIER")
    carrier.transport_task = TransportTask("water", well_a, bakery)
    carrier.carrying = "water"
    workers.add_worker(carrier)

    workers.update(0)

    queued_water = [
        task
        for task in workers._transport_queue  # noqa: SLF001
        if task.resource == "water" and task.target is bakery
    ]
    assert len(queued_water) == 1
    assert bakery.water_amount() == bakery.water_capacity() - 2

