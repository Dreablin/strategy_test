"""Multi-Scientist linear research point scaling (T429)."""

from __future__ import annotations

from game.buildings.laboratory import Laboratory
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.research_point_production import research_points_for_elapsed_ms
from game.research_start import try_start_active_research
from game.research_state import ResearchState
from game.world import World
from game.workers import Worker, WorkerManager


def _clear_world(world: World) -> None:
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    world.refresh_passability_tile_caches()


def _setup(*, level: int = 3) -> tuple[WorkerManager, Laboratory, ResearchState]:
    world = World(world_seed=21)
    _clear_world(world)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    laboratory = registry.place(Laboratory, near_town_hall_tile(10, 10))
    laboratory.level = level
    laboratory.construction_site = None
    state = ResearchState()
    try_start_active_research("1", research_state=state, registry=registry)
    workers = WorkerManager(registry, now_ms_fn=lambda: 0, research_state=state)
    return workers, laboratory, state


def _fill_laboratory_inputs(laboratory: Laboratory) -> None:
    for resource in laboratory.research_input_resources():
        laboratory.add_research_input(
            resource,
            laboratory.research_input_capacity(resource),
        )


def _hire_scientists(workers: WorkerManager, count: int) -> list[Worker]:
    hired: list[Worker] = []
    for _ in range(count):
        scientist = workers.hire("SCIENTIST")
        assert scientist is not None
        hired.append(scientist)
    return hired


def test_points_cap_at_laboratory_slot_capacity() -> None:
    _, laboratory, _ = _setup(level=3)
    rate = laboratory.research_points_per_scientist_per_second()
    capacity = laboratory.scientist_slot_capacity()
    assert capacity == 2
    at_capacity = research_points_for_elapsed_ms(
        laboratory=laboratory,
        active_scientist_count=capacity,
        elapsed_ms=1_000,
    )
    over_capacity = research_points_for_elapsed_ms(
        laboratory=laboratory,
        active_scientist_count=capacity + 3,
        elapsed_ms=1_000,
    )
    assert at_capacity == rate * capacity
    assert over_capacity == rate * capacity


def test_worker_manager_two_scientists_double_point_rate() -> None:
    workers, laboratory, state = _setup(level=3)
    _fill_laboratory_inputs(laboratory)
    _hire_scientists(workers, 2)
    workers.reassign_all()
    assert workers.laboratory_active_scientist_count(laboratory) == 2

    workers.update(0)
    workers.update(1_000)

    rate = laboratory.research_points_per_scientist_per_second()
    assert state.accumulated_points() == rate * 2


def test_worker_manager_max_slot_scientists_scale_linearly() -> None:
    workers, laboratory, state = _setup(level=10)
    _fill_laboratory_inputs(laboratory)
    capacity = laboratory.scientist_slot_capacity()
    assert capacity == 5
    _hire_scientists(workers, capacity)
    workers.reassign_all()
    assert workers.laboratory_active_scientist_count(laboratory) == capacity

    workers.update(0)
    workers.update(1_000)

    rate = laboratory.research_points_per_scientist_per_second()
    assert state.accumulated_points() == rate * capacity
