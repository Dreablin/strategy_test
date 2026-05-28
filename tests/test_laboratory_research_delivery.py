"""Carrier delivery into Laboratory research input storage (T425)."""

from __future__ import annotations

import pytest

from game.buildings.laboratory import Laboratory
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.research_start import try_start_active_research
from game.research_state import ResearchState
from game.world import World
from game.workers import WorkerManager


def _setup() -> tuple[BuildingRegistry, TownHall, Laboratory]:
    world = World(world_seed=3)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    laboratory = registry.place(Laboratory, near_town_hall_tile(10, 10))
    laboratory.construction_site = None
    try_start_active_research("1", research_state=ResearchState(), registry=registry)
    return registry, town_hall, laboratory


def test_add_research_input_rejects_unknown_and_overfill() -> None:
    _, _, laboratory = _setup()
    with pytest.raises(ValueError, match="not required"):
        laboratory.add_research_input("wine", 1)
    laboratory.add_research_input("wood", laboratory.research_input_capacity("wood"))
    with pytest.raises(ValueError, match="fully delivered"):
        laboratory.add_research_input("wood", 1)


def test_carrier_delivers_wood_to_laboratory_research_storage() -> None:
    registry, town_hall, laboratory = _setup()
    town_hall.add_to_warehouse("wood", 1)
    wm = WorkerManager(registry, now_ms_fn=lambda: 0)
    carrier = wm.hire("CARRIER")
    assert carrier is not None
    wm.enqueue_transport_task(
        resource="wood",
        source=town_hall,
        target=laboratory,
        amount=1,
        purpose="laboratory_research",
    )

    for now_ms in range(0, 120_000, 500):
        wm.update(now_ms)
        if laboratory.research_input_amount("wood") >= 1:
            break

    assert laboratory.research_input_amount("wood") == 1
    assert town_hall.warehouse_amount("wood") == 0


def test_carrier_redirects_to_town_hall_when_laboratory_input_full() -> None:
    registry, town_hall, laboratory = _setup()
    town_hall.add_to_warehouse("wood", 1)
    wm = WorkerManager(registry, now_ms_fn=lambda: 0)
    carrier = wm.hire("CARRIER")
    assert carrier is not None
    wm.enqueue_transport_task(
        resource="wood",
        source=town_hall,
        target=laboratory,
        amount=1,
        purpose="laboratory_research",
    )

    loading_ms = None
    for now_ms in range(0, 120_000, 500):
        wm.update(now_ms)
        if carrier.state == "carrier_loading":
            loading_ms = now_ms
            break
    assert loading_ms is not None
    wm.update(loading_ms + 2_100)
    assert carrier.carrying == "wood"

    laboratory.add_research_input("wood", laboratory.research_input_capacity("wood"))

    for now_ms in range(loading_ms + 2_200, loading_ms + 120_000, 500):
        wm.update(now_ms)
        if carrier.transport_task is None and carrier.carrying is None:
            break

    assert laboratory.research_input_amount("wood") == laboratory.research_input_capacity("wood")
    assert town_hall.warehouse_amount("wood") == 1
