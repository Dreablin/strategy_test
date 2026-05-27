"""Laboratory research input transport planning tests (T424)."""

from __future__ import annotations

from game.buildings.laboratory import Laboratory
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.research_start import try_start_active_research
from game.research_state import ResearchState
from game.transport_tasks import laboratory_input_transport_tasks
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


def test_inbound_counts_prevent_over_planning() -> None:
    registry, town_hall, laboratory, _ = _setup()
    town_hall.add_to_warehouse("wood", 50)
    inbound = {(id(laboratory), "wood"): 20}
    tasks = laboratory_input_transport_tasks(registry, inbound_counts=inbound)
    wood_tasks = [t for t in tasks if t.resource == "wood"]
    assert wood_tasks == []


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
