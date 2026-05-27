"""Research completion when point requirements are met (T431)."""

from __future__ import annotations

from game.buildings.laboratory import Laboratory
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.research_completion import (
    active_research_required_points,
    try_complete_active_research,
)
from game.research_config import RESEARCH_BY_ID
from game.research_point_production import try_accumulate_research_points
from game.research_start import try_start_active_research
from game.research_state import ResearchState
from game.world import World
from game.workers import WorkerManager


def _setup(*, level: int = 1) -> tuple[BuildingRegistry, Laboratory, ResearchState]:
    world = World(world_seed=40)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    laboratory = registry.place(Laboratory, near_town_hall_tile(10, 10))
    laboratory.level = level
    laboratory.construction_site = None
    state = ResearchState()
    return registry, laboratory, state


def _fill_laboratory_inputs(laboratory: Laboratory) -> None:
    for resource in laboratory.research_input_resources():
        laboratory.add_research_input(
            resource,
            laboratory.research_input_capacity(resource),
        )


def test_try_complete_active_research_requires_point_threshold() -> None:
    registry, laboratory, state = _setup()
    try_start_active_research("1", research_state=state, registry=registry)
    required = RESEARCH_BY_ID["1"].required_points
    for resource, amount in RESEARCH_BY_ID["1"].resource_cost.items():
        state.add_delivered(resource, amount)
    state.add_points(required - 1)
    assert not try_complete_active_research(research_state=state, laboratory=laboratory)
    assert state.has_active_research()
    state.add_points(1)
    assert try_complete_active_research(research_state=state, laboratory=laboratory)
    assert state.is_completed("1")
    assert not state.has_active_research()
    assert state.accumulated_points() == 0
    assert not laboratory.has_research_input_storage()


def test_try_complete_via_accumulate_clears_laboratory_storage() -> None:
    registry, laboratory, state = _setup()
    try_start_active_research("1", research_state=state, registry=registry)
    _fill_laboratory_inputs(laboratory)
    required = active_research_required_points(state)
    assert required is not None
    added = try_accumulate_research_points(
        research_state=state,
        laboratory=laboratory,
        points=required,
    )
    assert added == required
    assert state.is_completed("1")
    assert not laboratory.has_research_input_storage()


def test_completed_research_allows_starting_next_eligible_research() -> None:
    registry, laboratory, state = _setup(level=3)
    try_start_active_research("1", research_state=state, registry=registry)
    required = RESEARCH_BY_ID["1"].required_points
    for resource, amount in RESEARCH_BY_ID["1"].resource_cost.items():
        state.add_delivered(resource, amount)
    state.add_points(required)
    try_complete_active_research(research_state=state, laboratory=laboratory)
    try_start_active_research("2", research_state=state, registry=registry)
    assert state.active_research_id() == "2"
    assert laboratory.has_research_input_storage()


def test_worker_manager_completes_research_when_points_reach_requirement() -> None:
    registry, laboratory, state = _setup(level=1)
    try_start_active_research("1", research_state=state, registry=registry)
    _fill_laboratory_inputs(laboratory)
    workers = WorkerManager(registry, now_ms_fn=lambda: 0, research_state=state)
    scientist = workers.hire("SCIENTIST")
    assert scientist is not None
    workers.assign_to_building(scientist, laboratory)
    required = RESEARCH_BY_ID["1"].required_points
    rate = laboratory.research_points_per_scientist_per_second()
    ticks_needed = (required + rate - 1) // rate
    now_ms = 0
    workers.update(0)
    for _ in range(ticks_needed):
        now_ms += 1_000
        workers.update(now_ms)
        if state.is_completed("1"):
            break
    assert state.is_completed("1")
    assert not state.has_active_research()
    assert not laboratory.has_research_input_storage()
