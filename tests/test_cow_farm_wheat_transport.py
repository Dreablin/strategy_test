"""Cow Farm wheat refill via Town Hall carriers (T306)."""

from __future__ import annotations

from game.buildings.cow_farm import CowFarm
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.transport_tasks import processor_input_transport_tasks
from game.world import World
from game.workers import WorkerManager


def test_processor_input_transport_tasks_include_cow_farm_wheat() -> None:
    world = World(world_seed=0)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    world._iron.clear()  # noqa: SLF001
    world._gold.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    th = registry.place(TownHall, town_hall_origin_tile())
    cow = registry.place(CowFarm, near_town_hall_tile(20, 8))
    cow.construction_site = None
    th.add_to_warehouse("wheat", 5)

    tasks = processor_input_transport_tasks(registry, "wheat")

    to_cow = [t for t in tasks if t.target is cow and t.resource == "wheat" and t.source is th]
    cap = cow.wheat_capacity()
    assert len(to_cow) == cap
    assert all(t.priority == 0 for t in to_cow)


def test_cow_farm_wheat_enqueue_respects_queued_inbound_cap() -> None:
    world = World(world_seed=1)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    world._iron.clear()  # noqa: SLF001
    world._gold.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    th = registry.place(TownHall, town_hall_origin_tile())
    cow = registry.place(CowFarm, near_town_hall_tile(21, 8))
    cow.construction_site = None
    th.add_to_warehouse("wheat", 20)
    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    workers.enqueue_transport_task(resource="wheat", source=th, target=cow, amount=2)

    workers.update(0)

    to_cow = [t for t in workers._transport_queue if t.target is cow and t.resource == "wheat" and t.source is th]  # noqa: SLF001
    assert len(to_cow) == cow.wheat_capacity()
