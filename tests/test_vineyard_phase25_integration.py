"""Phase 25 integration: vineyard growth, farmer harvest, carrier export to Town Hall (T337)."""

from __future__ import annotations

import pytest

from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.buildings.vineyard import Vineyard
from game.buildings.vineyard_farm import VineyardFarm
from game.config import building_int_setting, near_town_hall_tile, town_hall_origin_tile
from game.world import World
from game.workers import WorkerManager


@pytest.fixture
def fast_vineyard_growth(monkeypatch: pytest.MonkeyPatch) -> None:
    orig = building_int_setting

    def _fake(tag: str, *keys: str) -> int:
        if tag == "VINEYARD" and keys == ("growth", "stage_duration_ms"):
            return 1_000
        return int(orig(tag, *keys))

    monkeypatch.setattr("game.buildings.vineyard.building_int_setting", _fake)


@pytest.fixture
def fast_workers(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("game.worker_farming.worker_building_action_ms", lambda _type_tag: 80)
    monkeypatch.setattr("game.worker_farming.worker_building_rest_ms", lambda _type_tag: 0)
    monkeypatch.setattr("game.worker_models.WORKER_TILE_TRAVEL_MS", 40)
    monkeypatch.setattr("game.worker_constants.CARRIER_INTERACT_MS", 80)


def test_vineyard_growth_farmer_harvest_carrier_export_to_town_hall(
    fast_vineyard_growth: None,
    fast_workers: None,
) -> None:
    now_ms = {"t": 0}
    world = World(world_seed=0)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    world._iron.clear()  # noqa: SLF001
    world.refresh_passability_tile_caches()
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    town_hall.construction_site = None
    vf = registry.place(VineyardFarm, near_town_hall_tile(12, 8))
    vf.construction_site = None
    plot = registry.place(Vineyard, near_town_hall_tile(16, 8))
    plot.construction_site = None

    workers = WorkerManager(registry, now_ms_fn=lambda: now_ms["t"])
    for _ in range(20):
        now_ms["t"] += 1_000
        workers.reassign_all()
        workers.update(now_ms["t"])
        if plot.is_ripe():
            break
    assert plot.is_ripe(), "expected vineyard to ripen via WorkerManager growth ticks"

    farmer = workers.hire("FARMER")
    assert farmer is not None
    for _ in range(12_000):
        now_ms["t"] += 40
        workers.reassign_all()
        workers.update(now_ms["t"])
        if vf.grapes_amount() >= 1 and not plot.is_ripe():
            break
    assert vf.grapes_amount() >= 1
    assert not plot.is_ripe()
    assert plot.growth_stage_index() >= 1
    assert int(town_hall.warehouse_amount("grapes")) == 0

    # Stop refills so the carrier can drain the farm in bounded steps (integration focus).
    workers._workers = [w for w in workers._workers if w.type_tag != "FARMER"]  # noqa: SLF001
    workers.reassign_all()

    assert workers.hire("CARRIER") is not None
    for _ in range(25_000):
        now_ms["t"] += 40
        workers.reassign_all()
        workers.update(now_ms["t"])
        if int(town_hall.warehouse_amount("grapes")) >= 1 and vf.grapes_amount() == 0:
            break

    assert int(town_hall.warehouse_amount("grapes")) >= 1
    assert vf.grapes_amount() == 0
