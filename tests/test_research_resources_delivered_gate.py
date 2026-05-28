"""Resources-delivered gate before research points accumulate (T427)."""

from __future__ import annotations

import pytest

from game.buildings.laboratory import Laboratory
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.research_config import RESEARCH_BY_ID
from game.research_point_production import (
    research_points_may_accumulate,
    try_accumulate_research_points,
)
from game.research_start import try_start_active_research
from game.research_state import ResearchState
from game.world import World
from game.workers import WorkerManager


def _laboratory_with_active_research() -> tuple[Laboratory, ResearchState]:
    world = World(world_seed=11)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    laboratory = registry.place(Laboratory, near_town_hall_tile(10, 10))
    laboratory.construction_site = None
    state = ResearchState()
    try_start_active_research("1", research_state=state, registry=registry)
    return laboratory, state


def test_laboratory_all_research_inputs_delivered() -> None:
    laboratory, _ = _laboratory_with_active_research()
    assert not laboratory.all_research_inputs_delivered()
    for resource in laboratory.research_input_resources():
        laboratory.add_research_input(
            resource,
            laboratory.research_input_capacity(resource),
        )
    assert laboratory.all_research_inputs_delivered()


def test_research_points_may_accumulate_requires_full_laboratory_storage() -> None:
    laboratory, state = _laboratory_with_active_research()
    assert not research_points_may_accumulate(research_state=state, laboratory=laboratory)
    laboratory.add_research_input("wood", laboratory.research_input_capacity("wood"))
    assert not research_points_may_accumulate(research_state=state, laboratory=laboratory)
    laboratory.add_research_input("boards", laboratory.research_input_capacity("boards"))
    assert research_points_may_accumulate(research_state=state, laboratory=laboratory)


def test_try_accumulate_research_points_is_gated_stub() -> None:
    laboratory, state = _laboratory_with_active_research()
    assert try_accumulate_research_points(research_state=state, laboratory=laboratory, points=50) == 0
    assert state.accumulated_points() == 0
    for resource in laboratory.research_input_resources():
        laboratory.add_research_input(
            resource,
            laboratory.research_input_capacity(resource),
        )
    assert try_accumulate_research_points(research_state=state, laboratory=laboratory, points=50) == 50
    assert state.accumulated_points() == 50


def test_add_points_rejects_until_all_resources_delivered() -> None:
    state = ResearchState()
    state.start_research("1")
    with pytest.raises(ValueError, match="not fully delivered"):
        state.add_points(1)
    for resource, required in RESEARCH_BY_ID["1"].resource_cost.items():
        state.add_delivered(resource, required)
    state.add_points(100)
    assert state.accumulated_points() == 100


def _carrier_setup() -> tuple[BuildingRegistry, TownHall, Laboratory, ResearchState]:
    world = World(world_seed=12)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    laboratory = registry.place(Laboratory, near_town_hall_tile(10, 10))
    laboratory.construction_site = None
    state = ResearchState()
    try_start_active_research("1", research_state=state, registry=registry)
    return registry, town_hall, laboratory, state


def test_record_laboratory_research_delivery_syncs_state() -> None:
    registry, _, _, state = _carrier_setup()
    workers = WorkerManager(registry, research_state=state)
    workers._record_laboratory_research_delivery("wood", 1)  # noqa: SLF001
    assert state.delivered_amounts()["wood"] == 1


def test_carrier_delivery_syncs_research_state_delivered() -> None:
    registry, town_hall, laboratory, state = _carrier_setup()
    town_hall.add_to_warehouse("wood", 1)
    workers = WorkerManager(registry, now_ms_fn=lambda: 0, research_state=state)
    carrier = workers.hire("CARRIER")
    assert carrier is not None
    workers.enqueue_transport_task(
        resource="wood",
        source=town_hall,
        target=laboratory,
        amount=1,
        purpose="laboratory_research",
    )

    for now_ms in range(0, 120_000, 500):
        workers.update(now_ms)
        if laboratory.research_input_amount("wood") >= 1:
            break

    assert state.delivered_amounts().get("wood") == 1
