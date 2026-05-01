"""RED tests for farm wheat transport task generation (T237)."""

from __future__ import annotations

from game.buildings.farm import Farm
from game.buildings.lumber_camp import LumberCamp
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.world import World
from game.workers import WorkerManager


def test_worker_manager_enqueues_wheat_export_tasks_from_farm_storage() -> None:
    world = World(world_seed=5)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    farm = registry.place(Farm, near_town_hall_tile(10, 8))
    farm.construction_site = None
    farm.stored = 2
    workers = WorkerManager(registry, now_ms_fn=lambda: 0)

    workers.update(0)

    wheat_tasks = [
        t for t in workers._transport_queue  # noqa: SLF001
        if t.resource == "wheat" and t.source is farm and t.target is town_hall
    ]
    assert len(wheat_tasks) == 2
    assert all(int(t.priority) == 0 for t in wheat_tasks)


def test_construction_transport_priority_stays_above_farm_wheat_exports() -> None:
    world = World(world_seed=6)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    town_hall.add_to_warehouse("wood", 5)
    farm = registry.place(Farm, near_town_hall_tile(10, 8))
    farm.construction_site = None
    farm.stored = 1
    camp = registry.place(LumberCamp, near_town_hall_tile(14, 8))
    workers = WorkerManager(registry, now_ms_fn=lambda: 0)

    workers.update(0)

    has_construction_task = any(
        t.resource == "wood" and t.target is camp and int(t.priority) == 10
        for t in workers._transport_queue  # noqa: SLF001
    )
    has_wheat_task = any(
        t.resource == "wheat" and t.source is farm and t.target is town_hall and int(t.priority) == 0
        for t in workers._transport_queue  # noqa: SLF001
    )
    assert has_construction_task
    assert has_wheat_task
