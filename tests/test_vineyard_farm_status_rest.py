"""Vineyard Farm farmer rest rhythm and panel status parity with wheat Farm (T331)."""

from __future__ import annotations

import pytest

from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.buildings.vineyard import Vineyard
from game.buildings.vineyard_farm import VineyardFarm
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.world import World
from game.worker_models import Worker
from game.workers import WorkerManager


@pytest.fixture
def fast_farmer(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("game.worker_farming.worker_building_action_ms", lambda _type_tag: 80)
    monkeypatch.setattr("game.worker_models.WORKER_TILE_TRAVEL_MS", 40)


def test_vineyard_farmer_rest_timer_after_grape_harvest_matches_farmer_rest_ms(
    fast_farmer: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("game.worker_farming.worker_building_rest_ms", lambda _type_tag: 5_000)
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
    for _ in range(12_000):
        now_ms["t"] += 40
        workers.reassign_all()
        workers.update(now_ms["t"])
        if vf.grapes_amount() == 1 and farmer.state == "resting":
            assert farmer.camp_wait_until_ms == now_ms["t"] + 5_000
            break
    else:
        pytest.fail("expected harvest completion into resting with one grape")

    before = now_ms["t"]
    now_ms["t"] += 39
    workers.reassign_all()
    workers.update(now_ms["t"])
    assert farmer.state == "resting"
    assert farmer.camp_wait_until_ms == before + 5_000
    assert farmer.state != "going_to_vineyard"


def test_vineyard_farm_production_status_reports_worker_action_states_and_hints() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    vf = registry.place(VineyardFarm, near_town_hall_tile(10, 8))
    vf.construction_site = None
    plot = registry.place(Vineyard, near_town_hall_tile(7, 8))
    plot.construction_site = None
    plot.set_growth_stage(4, now_ms=0)

    wm = WorkerManager(registry, now_ms_fn=lambda: 0)
    farmer = Worker("FARMER")
    wm.add_worker(farmer)
    wm.assign_to_building(farmer, vf)

    farmer.state = "moving"
    assert wm.production_status_for_building(vf) == "Moving"
    farmer.state = "going_to_vineyard"
    assert wm.production_status_for_building(vf) == "Moving"
    farmer.state = "returning"
    assert wm.production_status_for_building(vf) == "Moving"
    farmer.state = "harvesting_grapes"
    assert wm.production_status_for_building(vf) == "Harvesting"
    farmer.state = "vineyard_harvest_anim_done"
    assert wm.production_status_for_building(vf) == "Harvesting"

    vf.grapes_in = vf.grapes_capacity()
    farmer.state = "resting"
    assert wm.production_status_for_building(vf) == "Storage full"

    vf.grapes_in = 0
    plot.set_growth_stage(1, now_ms=0)
    farmer.state = "working_field"
    assert wm.production_status_for_building(vf) == "No ripe vineyards in range"
    plot.set_growth_stage(4, now_ms=0)
    assert wm.production_status_for_building(vf) == "Resting"

    farmer.state = "working"
    farmer.camp_wait_until_ms = 9_999
    assert wm.production_status_for_building(vf) == "Resting"
    farmer.camp_wait_until_ms = 0
    assert wm.production_status_for_building(vf) == "Ready"

    vf.set_active(False)
    assert wm.production_status_for_building(vf) == "Inactive"


def test_vineyard_farm_worker_status_reports_farm_style_buckets() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    vf = registry.place(VineyardFarm, near_town_hall_tile(10, 8))
    vf.construction_site = None
    plot = registry.place(Vineyard, near_town_hall_tile(7, 8))
    plot.construction_site = None
    plot.set_growth_stage(4, now_ms=0)

    wm = WorkerManager(registry)
    farmer = Worker("FARMER")
    wm.add_worker(farmer)
    wm.assign_to_building(farmer, vf)

    farmer.state = "going_to_vineyard"
    assert wm.worker_status_for_building(vf) == "moving"
    farmer.state = "harvesting_grapes"
    assert wm.worker_status_for_building(vf) == "harvesting"
    farmer.state = "vineyard_harvest_anim_done"
    assert wm.worker_status_for_building(vf) == "harvesting"
    farmer.state = "working_field"
    assert wm.worker_status_for_building(vf) == "resting"
