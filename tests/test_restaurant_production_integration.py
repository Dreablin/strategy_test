"""Focused Restaurant production integration test (T384).

Covers:
  1. Inputs (bread, wine, beef) reach a built Restaurant via transport tasks.
  2. An assigned Cook produces elite_meal from those inputs.
  3. elite_meal is never exported to the Town Hall warehouse.
"""

from __future__ import annotations

from game.buildings.registry import BuildingRegistry
from game.buildings.restaurant import Restaurant
from game.buildings.town_hall import TownHall
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.transport_tasks import restaurant_input_transport_tasks
from game.workers import WorkerManager
from game.world import World


def _setup():
    world = World(world_seed=0)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    world._iron.clear()  # noqa: SLF001
    world.refresh_passability_tile_caches()
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    restaurant = registry.place(Restaurant, near_town_hall_tile(5, 5))
    restaurant.construction_site = None
    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    cook = workers.hire("COOK")
    assert cook is not None
    workers.reassign_all()
    assert cook.assigned_building is restaurant
    return world, registry, town_hall, restaurant, workers, cook


def test_restaurant_production_integration() -> None:
    """End-to-end: inputs arrive → Cook produces elite_meal → no TH export."""
    world, registry, town_hall, restaurant, workers, cook = _setup()

    town_hall.add_to_warehouse("bread", 3)
    town_hall.add_to_warehouse("wine", 3)
    town_hall.add_to_warehouse("beef", 3)
    for res in ("bread", "wine", "beef"):
        tasks = restaurant_input_transport_tasks(registry, res)
        assert len(tasks) > 0, f"Expected transport tasks for {res}"
        for t in tasks:
            assert t.target is restaurant
            assert t.source is town_hall

    restaurant.add_local_storage("bread", 1)
    restaurant.add_local_storage("wine", 1)
    restaurant.add_local_storage("beef", 1)

    now_ms = 0
    started_processing = False
    for _ in range(200):
        now_ms += 500
        workers.update(now_ms)
        if cook.state == "processing":
            started_processing = True
            break
    assert started_processing, f"Cook did not start processing; state={cook.state}"

    now_ms += 60_000
    workers.update(now_ms)
    produced = restaurant.local_storage_amount("elite_meal")
    assert produced >= 1, f"Expected at least 1 elite_meal, got {produced}"

    assert town_hall.warehouse_amount("elite_meal") == 0, (
        "elite_meal must not be exported to Town Hall"
    )

    from game.resource_catalog import is_local_only_meal
    assert is_local_only_meal("elite_meal")
    elite_tasks = restaurant_input_transport_tasks(registry, "elite_meal")
    assert elite_tasks == [], "elite_meal should not generate inbound transport tasks"
