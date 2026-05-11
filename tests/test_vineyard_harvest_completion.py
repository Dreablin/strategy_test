"""Vineyard harvest completes into Vineyard Farm storage (T330)."""

from __future__ import annotations

import pytest

from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.buildings.vineyard import Vineyard
from game.buildings.vineyard_farm import VineyardFarm
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.worker_geometry import building_center_tile
from game.world import World
from game.workers import WorkerManager


@pytest.fixture
def fast_farmer_and_travel(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("game.worker_farming.FARMER_ACTION_MS", 80)
    monkeypatch.setattr("game.worker_farming.FARMER_REST_MS", 0)
    monkeypatch.setattr("game.worker_models.WORKER_TILE_TRAVEL_MS", 40)


def test_vineyard_harvest_adds_grape_resets_plot_releases_reservation(
    fast_farmer_and_travel: None,
) -> None:
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
    assert plot.grid_pos in workers._vineyard_plot_reservations  # noqa: SLF001

    now_ms["t"] += 40
    workers.reassign_all()
    workers.update(now_ms["t"])

    harvest_tile = farmer.current_tile
    assert farmer.state == "returning"
    assert farmer.current_tile == harvest_tile
    assert farmer.current_tile != building_center_tile(vf)
    assert farmer.carrying == "grapes"
    assert vf.grapes_amount() == 0
    assert not plot.is_ripe()
    assert plot.grid_pos not in workers._vineyard_plot_reservations  # noqa: SLF001

    for _ in range(400):
        now_ms["t"] += 40
        workers.reassign_all()
        workers.update(now_ms["t"])
        if farmer.state == "resting":
            break

    assert farmer.state == "resting"
    assert vf.grapes_amount() == 1
    assert farmer.carrying is None
    assert farmer.target_tree is None


def test_vineyard_harvest_storage_full_skips_deposit_plot_stays_ripe(
    fast_farmer_and_travel: None,
) -> None:
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
        if farmer.state == "harvesting_grapes":
            vf.grapes_in = vf.grapes_capacity()
            break

    for _ in range(200):
        now_ms["t"] += 40
        workers.reassign_all()
        workers.update(now_ms["t"])
        if farmer.state == "vineyard_harvest_anim_done":
            break
    assert farmer.state == "vineyard_harvest_anim_done"

    now_ms["t"] += 40
    workers.reassign_all()
    workers.update(now_ms["t"])

    assert farmer.state == "returning"
    assert vf.grapes_amount() == vf.grapes_capacity()
    assert plot.is_ripe()
    assert farmer.target_tree is None
    assert plot.grid_pos not in workers._vineyard_plot_reservations  # noqa: SLF001

    for _ in range(400):
        now_ms["t"] += 40
        workers.reassign_all()
        workers.update(now_ms["t"])
        if farmer.state == "resting":
            break

    assert farmer.state == "resting"
    assert farmer.carrying is None
