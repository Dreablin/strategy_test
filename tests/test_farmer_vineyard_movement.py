"""Farmer walks to ripe vineyards when assigned to Vineyard Farm (T329)."""

from __future__ import annotations

import pytest

from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.buildings.vineyard import Vineyard
from game.buildings.vineyard_farm import VineyardFarm
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.world import World
from game.workers import WorkerManager


@pytest.fixture
def fast_farmer_and_travel(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("game.worker_farming.worker_building_action_ms", lambda _type_tag: 80)
    monkeypatch.setattr("game.worker_farming.worker_building_rest_ms", lambda _type_tag: 0)
    monkeypatch.setattr("game.worker_models.WORKER_TILE_TRAVEL_MS", 40)


def test_farmer_reaches_harvesting_grapes_at_ripe_vineyard(fast_farmer_and_travel: None) -> None:
    now_ms = {"t": 0}
    world = World(world_seed=0)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    world._iron.clear()  # noqa: SLF001
    world.refresh_passability_tile_caches()
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    vf = registry.place(VineyardFarm, near_town_hall_tile(12, 8))
    vf.construction_site = None
    plot = registry.place(Vineyard, near_town_hall_tile(16, 8))
    plot.construction_site = None
    plot.set_growth_stage(4, now_ms=0)

    workers = WorkerManager(registry, now_ms_fn=lambda: now_ms["t"])
    farmer = workers.hire("FARMER")
    assert farmer is not None
    for _ in range(6000):
        now_ms["t"] += 40
        workers.reassign_all()
        workers.update(now_ms["t"])
        if farmer.assigned_building is vf and farmer.state in {
            "going_to_vineyard",
            "arrived_vineyard",
            "harvesting_grapes",
            "vineyard_harvest_anim_done",
        }:
            break
    assert farmer.assigned_building is vf
    assert farmer.state in {
        "going_to_vineyard",
        "arrived_vineyard",
        "harvesting_grapes",
        "vineyard_harvest_anim_done",
    }
    assert farmer.target_tree == plot.grid_pos
    if farmer.state in {"arrived_vineyard", "harvesting_grapes", "vineyard_harvest_anim_done"}:
        assert farmer.current_tile == plot.grid_pos


def test_farmer_reaches_vineyard_harvest_anim_done(fast_farmer_and_travel: None) -> None:
    now_ms = {"t": 0}
    world = World(world_seed=0)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    world._iron.clear()  # noqa: SLF001
    world.refresh_passability_tile_caches()
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    vf = registry.place(VineyardFarm, near_town_hall_tile(12, 8))
    vf.construction_site = None
    plot = registry.place(Vineyard, near_town_hall_tile(16, 8))
    plot.construction_site = None
    plot.set_growth_stage(4, now_ms=0)

    workers = WorkerManager(registry, now_ms_fn=lambda: now_ms["t"])
    farmer = workers.hire("FARMER")
    assert farmer is not None
    for _ in range(8000):
        now_ms["t"] += 40
        workers.reassign_all()
        workers.update(now_ms["t"])
        if farmer.state == "vineyard_harvest_anim_done":
            break
    assert farmer.state == "vineyard_harvest_anim_done"
    assert plot.is_ripe()
    assert farmer.target_tree == plot.grid_pos
    assert farmer.current_tile == plot.grid_pos

    now_ms["t"] += 40
    workers.reassign_all()
    workers.update(now_ms["t"])
    assert farmer.state == "returning"
    assert farmer.carrying == "grapes"
    assert vf.grapes_amount() == 0
    assert not plot.is_ripe()

    for _ in range(400):
        now_ms["t"] += 40
        workers.reassign_all()
        workers.update(now_ms["t"])
        if farmer.state == "resting":
            break

    assert farmer.state == "resting"
    assert vf.grapes_amount() == 1
    assert farmer.target_tree is None
