"""Scientists absent from the Laboratory do not contribute research points (T430)."""

from __future__ import annotations

from game.buildings.canteen import Canteen
from game.buildings.laboratory import Laboratory
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.worker_laboratory import (
    laboratory_research_contributing_scientist_count,
    scientist_contributes_to_research_points,
)
from game.research_start import try_start_active_research
from game.research_state import ResearchState
from game.world import World
from game.workers import Worker, WorkerManager


def _setup(*, level: int = 3) -> tuple[WorkerManager, Laboratory, ResearchState, Canteen]:
    world = World(world_seed=30)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    laboratory = registry.place(Laboratory, near_town_hall_tile(10, 10))
    laboratory.level = level
    laboratory.construction_site = None
    canteen = registry.place(Canteen, near_town_hall_tile(14, 10))
    canteen.construction_site = None
    state = ResearchState()
    try_start_active_research("1", research_state=state, registry=registry)
    workers = WorkerManager(registry, now_ms_fn=lambda: 0, research_state=state)
    return workers, laboratory, state, canteen


def _fill_laboratory_inputs(laboratory: Laboratory) -> None:
    for resource in laboratory.research_input_resources():
        laboratory.add_research_input(
            resource,
            laboratory.research_input_capacity(resource),
        )


def _hire_and_assign(workers: WorkerManager, laboratory: Laboratory, count: int) -> list[Worker]:
    hired: list[Worker] = []
    for _ in range(count):
        scientist = workers.hire("SCIENTIST")
        assert scientist is not None
        workers.assign_to_building(scientist, laboratory)
        hired.append(scientist)
    return hired


def test_working_scientist_inside_laboratory_contributes() -> None:
    workers, laboratory, _, _ = _setup()
    scientists = _hire_and_assign(workers, laboratory, 1)
    scientist = scientists[0]
    assert scientist_contributes_to_research_points(scientist, laboratory)
    assert laboratory_research_contributing_scientist_count(workers._workers, laboratory) == 1  # noqa: SLF001


def test_dining_scientist_does_not_contribute() -> None:
    workers, laboratory, _, canteen = _setup()
    scientists = _hire_and_assign(workers, laboratory, 2)
    dining = scientists[0]
    dining.dining_canteen = canteen
    dining.dining_phase = "eating"
    dining.state = "eating"
    dining.idle = False
    assert not scientist_contributes_to_research_points(dining, laboratory)
    assert laboratory_research_contributing_scientist_count(workers._workers, laboratory) == 1  # noqa: SLF001


def test_walking_to_diner_and_returning_scientists_do_not_contribute() -> None:
    workers, laboratory, _, canteen = _setup()
    scientists = _hire_and_assign(workers, laboratory, 2)
    walking = scientists[0]
    walking.dining_canteen = canteen
    walking.dining_phase = "walking_to_diner"
    walking.state = "going_to_canteen"
    walking.idle = False
    assert not scientist_contributes_to_research_points(walking, laboratory)

    returning = scientists[1]
    returning.dining_canteen = canteen
    returning.dining_phase = "returning_to_work"
    returning.state = "moving"
    returning.idle = False
    assert not scientist_contributes_to_research_points(returning, laboratory)


def test_idle_unassigned_scientist_does_not_contribute() -> None:
    workers, laboratory, _, _ = _setup()
    scientist = workers.hire("SCIENTIST")
    assert scientist is not None
    scientist.idle = True
    scientist.state = "idle"
    assert not scientist_contributes_to_research_points(scientist, laboratory)


def test_scientist_outside_laboratory_footprint_does_not_contribute() -> None:
    workers, laboratory, _, _ = _setup()
    scientists = _hire_and_assign(workers, laboratory, 1)
    scientist = scientists[0]
    scientist.current_tile = near_town_hall_tile(20, 20)
    assert not scientist_contributes_to_research_points(scientist, laboratory)


def test_worker_manager_ignores_dining_scientist_for_point_rate() -> None:
    workers, laboratory, state, canteen = _setup()
    _fill_laboratory_inputs(laboratory)
    scientists = _hire_and_assign(workers, laboratory, 2)
    dining = scientists[0]
    dining.dining_canteen = canteen
    dining.dining_phase = "eating"
    dining.state = "eating"
    dining.idle = False

    workers.update(0)
    workers.update(1_000)

    rate = laboratory.research_points_per_scientist_per_second()
    assert workers.laboratory_active_scientist_count(laboratory) == 2
    assert workers.laboratory_research_contributing_scientist_count(laboratory) == 1
    assert state.accumulated_points() == rate
