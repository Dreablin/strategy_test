"""Laboratory research input transport planning tests (T424)."""

from __future__ import annotations

from game.buildings.laboratory import Laboratory
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.buildings.well import Well
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.research_config import RESEARCH_BY_ID
from game.research_start import try_start_active_research
from game.research_state import ResearchState
from game.transport_tasks import laboratory_input_transport_tasks
from game.worker_models import TransportTask, Worker
from game.world import World
from game.workers import WorkerManager


def _setup() -> tuple[BuildingRegistry, TownHall, Laboratory, ResearchState]:
    world = World(world_seed=0)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    laboratory = registry.place(Laboratory, near_town_hall_tile(10, 10))
    laboratory.construction_site = None
    state = ResearchState()
    try_start_active_research("1", research_state=state, registry=registry)
    return registry, town_hall, laboratory, state


def test_laboratory_input_tasks_from_town_hall_for_active_research() -> None:
    registry, town_hall, laboratory, _ = _setup()
    town_hall.add_to_warehouse("wood", 25)
    town_hall.add_to_warehouse("boards", 15)
    tasks = laboratory_input_transport_tasks(registry)
    wood_tasks = [t for t in tasks if t.resource == "wood" and t.target is laboratory]
    board_tasks = [t for t in tasks if t.resource == "boards" and t.target is laboratory]
    assert len(wood_tasks) == 20
    assert len(board_tasks) == 10
    assert all(t.source is town_hall for t in wood_tasks + board_tasks)
    assert all(t.purpose == "laboratory_research" for t in tasks)


def test_laboratory_input_tasks_skip_inactive_laboratory() -> None:
    registry, town_hall, laboratory, _ = _setup()
    town_hall.add_to_warehouse("wood", 25)
    town_hall.add_to_warehouse("boards", 15)
    laboratory.set_active(False)

    assert laboratory_input_transport_tasks(registry) == []


def test_inbound_counts_prevent_over_planning() -> None:
    registry, town_hall, laboratory, _ = _setup()
    town_hall.add_to_warehouse("wood", 50)
    inbound = {(id(laboratory), "wood"): 20}
    tasks = laboratory_input_transport_tasks(registry, inbound_counts=inbound)
    wood_tasks = [t for t in tasks if t.resource == "wood"]
    assert wood_tasks == []


def test_laboratory_water_input_tasks_use_well_local_storage() -> None:
    registry, town_hall, laboratory, state = _setup()
    state.cancel_active_research()
    state.start_research("1")
    state.mark_research_completed("1")
    state.start_research("carrier_speed_1")
    laboratory.initialize_research_input_storage(RESEARCH_BY_ID["carrier_speed_1"].resource_cost)
    town_hall.add_to_warehouse("hide", 4)
    well = registry.place(Well, near_town_hall_tile(14, 10))
    well.level = 5
    well.construction_site = None
    well.add_water_in(5)

    tasks = laboratory_input_transport_tasks(registry)

    water_tasks = [task for task in tasks if task.resource == "water"]
    hide_tasks = [task for task in tasks if task.resource == "hide"]
    assert len(water_tasks) == 5
    assert all(task.source is well and task.target is laboratory for task in water_tasks)
    assert all(task.purpose == "laboratory_research" for task in water_tasks)
    assert len(hide_tasks) == 4
    assert all(task.source is town_hall and task.target is laboratory for task in hide_tasks)


def test_no_tasks_without_active_research_storage() -> None:
    world = World(world_seed=1)
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    laboratory = registry.place(Laboratory, near_town_hall_tile(12, 10))
    laboratory.construction_site = None
    town_hall.add_to_warehouse("wood", 10)
    assert laboratory_input_transport_tasks(registry) == []


def test_worker_manager_enqueues_laboratory_research_tasks() -> None:
    registry, town_hall, laboratory, _ = _setup()
    town_hall.add_to_warehouse("wood", 5)
    town_hall.add_to_warehouse("boards", 5)
    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    workers.update(0)
    queued = [
        t
        for t in workers._transport_queue  # noqa: SLF001
        if t.purpose == "laboratory_research" and t.target is laboratory
    ]
    assert len(queued) == 10
    assert {t.resource for t in queued} == {"wood", "boards"}


def test_worker_manager_removes_queued_laboratory_tasks_when_laboratory_inactive() -> None:
    registry, town_hall, laboratory, _ = _setup()
    town_hall.add_to_warehouse("wood", 5)
    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    workers.enqueue_transport_task(
        resource="wood",
        source=town_hall,
        target=laboratory,
        priority=0,
        purpose="laboratory_research",
    )

    laboratory.set_active(False)
    workers.update(0)

    assert not [
        task
        for task in workers._transport_queue  # noqa: SLF001
        if task.purpose == "laboratory_research" and task.target is laboratory
    ]


def test_inactive_laboratory_cancels_assigned_research_task_before_pickup() -> None:
    registry, town_hall, laboratory, _ = _setup()
    carrier = Worker("CARRIER", stand_tile=town_hall.grid_pos)
    task = TransportTask("wood", town_hall, laboratory, purpose="laboratory_research")
    carrier.transport_task = task
    carrier.carrying = None
    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    workers._workers.append(carrier)  # noqa: SLF001

    laboratory.set_active(False)
    workers.update(0)

    assert carrier.transport_task is None
    assert carrier.carrying is None
    assert carrier.idle is True


def test_inactive_laboratory_keeps_carried_research_delivery_assigned() -> None:
    registry, town_hall, laboratory, _ = _setup()
    carrier = Worker("CARRIER", stand_tile=town_hall.grid_pos)
    task = TransportTask("wood", town_hall, laboratory, purpose="laboratory_research")
    carrier.transport_task = task
    carrier.carrying = "wood"
    carrier.state = "moving"
    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    workers._workers.append(carrier)  # noqa: SLF001

    laboratory.set_active(False)
    workers.update(0)

    assert carrier.transport_task is task
    assert carrier.carrying == "wood"
