"""Phase 26 integration: grapes into Winery, Winemaker produces wine, carrier exports to Town Hall (T358)."""

from __future__ import annotations

import pytest

from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.buildings.winery import Winery
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.workers import WorkerManager
from game.world import World


@pytest.fixture
def fast_workers(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("game.worker_models.WORKER_TILE_TRAVEL_MS", 40)
    monkeypatch.setattr("game.worker_constants.CARRIER_INTERACT_MS", 80)


def test_grapes_to_winery_production_to_town_hall(fast_workers: None) -> None:
    """End-to-end: Town Hall grapes → carrier → Winery → Winemaker → wine → carrier → Town Hall."""
    world = World(world_seed=0)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    world._iron.clear()  # noqa: SLF001
    world.refresh_passability_tile_caches()

    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())

    winery = registry.place(Winery, near_town_hall_tile(5, 5))
    winery.construction_site = None
    recipe_input = winery.recipe_input_count()
    recipe_output = winery.recipe_output_count()
    town_hall.add_to_warehouse("grapes", recipe_input)

    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    winemaker = workers.hire("WINEMAKER")
    carrier = workers.hire("CARRIER")
    assert winemaker is not None
    assert carrier is not None
    workers.reassign_all()

    # Phase 1: Carrier delivers grapes from TH to Winery
    now_ms = 0
    grapes_arrived = False
    for _ in range(4000):
        now_ms += 100
        workers.update(now_ms)
        if winery.input_amount() >= recipe_input:
            grapes_arrived = True
            break
    assert grapes_arrived, f"Grapes did not arrive at winery; input={winery.input_amount()}"

    # Phase 2: Winemaker processes grapes into wine (60s cycle)
    production_done = False
    for _ in range(4000):
        now_ms += 100
        workers.update(now_ms)
        if winery.output_amount() >= recipe_output:
            production_done = True
            break
    assert production_done, f"Winemaker did not produce wine; output={winery.output_amount()}"

    # Phase 3: Carrier exports wine from Winery to Town Hall
    wine_exported = False
    for _ in range(4000):
        now_ms += 100
        workers.update(now_ms)
        if town_hall.warehouse_amount("wine") >= 1:
            wine_exported = True
            break
    assert wine_exported, f"Wine not exported; TH wine={town_hall.warehouse_amount('wine')}, winery wine={winery.output_amount()}"
