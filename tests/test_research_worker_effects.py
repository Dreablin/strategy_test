"""Completed research worker effects."""

from __future__ import annotations

import pytest

from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.config import town_hall_origin_tile
from game.research_state import ResearchState
from game.worker_models import Worker
from game.world import World
from game.workers import WorkerManager


def _completed_carrier_speed_state() -> ResearchState:
    state = ResearchState()
    state.start_research("carrier_speed_1")
    state.mark_research_completed("carrier_speed_1")
    return state


def test_completed_carrier_speed_research_applies_to_existing_carriers() -> None:
    state = _completed_carrier_speed_state()
    workers = WorkerManager(research_state=state)
    carrier = Worker("CARRIER")
    builder = Worker("BUILDER")
    workers.add_worker(carrier)
    workers.add_worker(builder)

    workers.update(0)

    assert carrier.characteristics.move_speed_mult == pytest.approx(1.1)
    assert builder.characteristics.move_speed_mult == pytest.approx(1.0)


def test_completed_carrier_speed_research_applies_to_new_hires() -> None:
    world = World(world_seed=0)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    world._iron.clear()  # noqa: SLF001
    world.refresh_passability_tile_caches()
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    workers = WorkerManager(registry, research_state=_completed_carrier_speed_state())

    carrier = workers.hire("CARRIER")

    assert carrier is not None
    assert carrier.characteristics.move_speed_mult == pytest.approx(1.1)
