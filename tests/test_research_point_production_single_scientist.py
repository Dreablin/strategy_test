"""Single-Scientist research point production over elapsed time (T428)."""

from __future__ import annotations

from game.buildings.laboratory import Laboratory
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.research_point_production import (
    research_points_for_elapsed_ms,
    tick_laboratory_research_points,
)
from game.research_start import try_start_active_research
from game.research_state import ResearchState
from game.world import World
from game.workers import WorkerManager


def _setup() -> tuple[WorkerManager, Laboratory, ResearchState]:
    world = World(world_seed=20)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    laboratory = registry.place(Laboratory, near_town_hall_tile(10, 10))
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


def test_research_points_for_elapsed_ms_uses_configured_rate() -> None:
    _, laboratory, _ = _setup()
    rate = laboratory.research_points_per_scientist_per_second()
    assert research_points_for_elapsed_ms(
        laboratory=laboratory,
        active_scientist_count=1,
        elapsed_ms=1_000,
    ) == rate
    assert research_points_for_elapsed_ms(
        laboratory=laboratory,
        active_scientist_count=0,
        elapsed_ms=1_000,
    ) == 0


def test_research_points_cap_at_single_scientist_for_t428() -> None:
    _, laboratory, _ = _setup()
    rate = laboratory.research_points_per_scientist_per_second()
    one = research_points_for_elapsed_ms(
        laboratory=laboratory,
        active_scientist_count=1,
        elapsed_ms=1_000,
    )
    two = research_points_for_elapsed_ms(
        laboratory=laboratory,
        active_scientist_count=3,
        elapsed_ms=1_000,
    )
    assert one == rate
    assert two == rate


def test_tick_laboratory_research_points_requires_delivered_inputs() -> None:
    _, laboratory, state = _setup()
    last_ticks: dict[int, int] = {}
    tick_laboratory_research_points(
        research_state=state,
        laboratory=laboratory,
        active_scientist_count=1,
        now_ms=0,
        last_tick_by_laboratory=last_ticks,
    )
    tick_laboratory_research_points(
        research_state=state,
        laboratory=laboratory,
        active_scientist_count=1,
        now_ms=1_000,
        last_tick_by_laboratory=last_ticks,
    )
    assert state.accumulated_points() == 0
    _fill_laboratory_inputs(laboratory)
    tick_laboratory_research_points(
        research_state=state,
        laboratory=laboratory,
        active_scientist_count=1,
        now_ms=2_000,
        last_tick_by_laboratory=last_ticks,
    )
    assert state.accumulated_points() == laboratory.research_points_per_scientist_per_second()


def test_worker_manager_accumulates_points_with_one_scientist() -> None:
    workers, laboratory, state = _setup()
    _fill_laboratory_inputs(laboratory)
    scientist = workers.hire("SCIENTIST")
    assert scientist is not None
    workers.reassign_all()
    assert workers.laboratory_active_scientist_count(laboratory) == 1

    workers.update(0)
    workers.update(1_000)

    assert state.accumulated_points() == laboratory.research_points_per_scientist_per_second()


def test_worker_manager_does_not_accumulate_without_scientist() -> None:
    workers, laboratory, state = _setup()
    _fill_laboratory_inputs(laboratory)

    workers.update(0)
    workers.update(2_000)

    assert state.accumulated_points() == 0
