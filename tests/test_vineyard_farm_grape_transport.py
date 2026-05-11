"""Vineyard Farm grape carrier export planning (T332)."""

from __future__ import annotations

from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.buildings.vineyard_farm import VineyardFarm
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.construction import ConstructionSite
from game.transport_tasks import vineyard_farm_grape_output_transport_tasks
from game.world import World
from game.worker_models import TransportTask, Worker
from game.workers import WorkerManager


def _advance_until_loading(workers: WorkerManager, carrier: Worker, *, max_steps: int = 200, step_ms: int = 500) -> None:
    now_ms = 0
    for _ in range(max_steps):
        workers.update(now_ms)
        if carrier.state == "carrier_loading":
            return
        now_ms += step_ms
    raise AssertionError("carrier never reached loading state")


def test_vineyard_farm_grape_transport_tasks_one_task_per_stored_grape() -> None:
    world = World(world_seed=1)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    vf = registry.place(VineyardFarm, near_town_hall_tile(10, 8))
    vf.construction_site = None
    vf.grapes_in = 2

    tasks = vineyard_farm_grape_output_transport_tasks(registry)
    assert len(tasks) == 2
    assert all(t.resource == "grapes" and t.source is vf and t.target is town_hall for t in tasks)
    assert all(int(t.priority) == 0 for t in tasks)


def test_vineyard_farm_grape_tasks_skip_inactive_under_construction_and_empty() -> None:
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    vf = registry.place(VineyardFarm, near_town_hall_tile(10, 8))
    vf.construction_site = None
    vf.grapes_in = 1
    assert len(vineyard_farm_grape_output_transport_tasks(registry)) == 1

    vf.set_active(False)
    assert vineyard_farm_grape_output_transport_tasks(registry) == []

    vf.set_active(True)
    vf.grapes_in = 0
    assert vineyard_farm_grape_output_transport_tasks(registry) == []

    vf.grapes_in = 1
    vf.construction_site = ConstructionSite(
        required_resources={"wood": 1},
        delivered_resources={},
        build_time_ms=1_000,
        build_started_ms=None,
        builder=None,
        target_level=1,
    )
    assert vineyard_farm_grape_output_transport_tasks(registry) == []


def test_worker_manager_enqueues_grape_exports_deduping_queue_and_assigned_carrier() -> None:
    world = World(world_seed=3)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    vf = registry.place(VineyardFarm, near_town_hall_tile(10, 8))
    vf.construction_site = None
    vf.grapes_in = 3

    wm = WorkerManager(registry, now_ms_fn=lambda: 0)
    wm.enqueue_transport_task(resource="grapes", source=vf, target=town_hall, amount=1)
    carrier = Worker("CARRIER")
    carrier.transport_task = TransportTask(resource="grapes", source=vf, target=town_hall)
    wm.add_worker(carrier)

    wm.update(0)

    queued = [t for t in wm._transport_queue if t.resource == "grapes" and t.source is vf]  # noqa: SLF001
    assert len(queued) == 2


def test_stale_vineyard_farm_grape_task_dropped_when_source_empty_at_pickup() -> None:
    world = World(world_seed=9)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    world._iron.clear()  # noqa: SLF001
    world._gold.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    vf = registry.place(VineyardFarm, near_town_hall_tile(10, 8))
    vf.construction_site = None
    vf.grapes_in = 1

    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    carrier = workers.hire("CARRIER")
    assert carrier is not None

    workers.enqueue_transport_task(resource="grapes", source=vf, target=town_hall, amount=1, priority=0)
    _advance_until_loading(workers, carrier)

    vf.grapes_in = 0
    carrier.camp_wait_until_ms = 0
    workers.update(5_000)

    assert carrier.transport_task is None
    assert carrier.state == "idle"
    assert not any(
        t.resource == "grapes" and t.source is vf and t.target is town_hall
        for t in workers._transport_queue  # noqa: SLF001
    )


def test_demolished_vineyard_farm_grape_tasks_removed_when_carrier_claims_next() -> None:
    world = World(world_seed=4)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    world._iron.clear()  # noqa: SLF001
    world._gold.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    vf = registry.place(VineyardFarm, near_town_hall_tile(10, 8))
    vf.construction_site = None
    vf.grapes_in = 1

    wm = WorkerManager(registry, now_ms_fn=lambda: 0)
    wm.update(0)
    assert any(t.resource == "grapes" and t.source is vf for t in wm._transport_queue)  # noqa: SLF001

    registry.demolish(vf, wm)
    carrier = wm.hire("CARRIER")
    assert carrier is not None
    wm.update(0)

    assert not any(t.resource == "grapes" for t in wm._transport_queue)  # noqa: SLF001
