"""Cow Farm hide export to Town Hall (T309)."""

from __future__ import annotations

from game.buildings.cow_farm import CowFarm
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.transport_tasks import cow_farm_hide_output_transport_tasks
from game.world import World
from game.workers import WorkerManager


def test_cow_farm_hide_output_transport_tasks_export_to_town_hall() -> None:
    world = World(world_seed=0)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    world._iron.clear()  # noqa: SLF001
    world._gold.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    th = registry.place(TownHall, town_hall_origin_tile())
    cow = registry.place(CowFarm, near_town_hall_tile(19, 8))
    cow.construction_site = None
    cow.add_hide_out(2)

    tasks = cow_farm_hide_output_transport_tasks(registry)
    hide = [t for t in tasks if t.resource == "hide" and t.source is cow and t.target is th]

    assert len(hide) == 2
    assert all(t.priority == 0 for t in hide)


def test_carrier_exports_hide_from_cow_farm_to_town_hall() -> None:
    world = World(world_seed=2)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    world._iron.clear()  # noqa: SLF001
    world._gold.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    th = registry.place(TownHall, town_hall_origin_tile())
    cow = registry.place(CowFarm, near_town_hall_tile(19, 8))
    cow.construction_site = None
    cow.add_hide_out(1)
    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    carrier = workers.hire("CARRIER")
    assert carrier is not None

    for now_ms in range(0, 220_000, 500):
        workers.update(now_ms)
        if th.warehouse_amount("hide") >= 1:
            break

    assert th.warehouse_amount("hide") == 1
    assert cow.hide_amount() == 0


def test_cow_farm_hide_export_enqueue_respects_queued_tasks() -> None:
    world = World(world_seed=0)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    world._iron.clear()  # noqa: SLF001
    world._gold.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    cow = registry.place(CowFarm, near_town_hall_tile(19, 8))
    cow.construction_site = None
    cow.add_hide_out(3)
    th = next(b for b in registry.all() if b.type_tag == "TOWN_HALL")
    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    workers.enqueue_transport_task(resource="hide", source=cow, target=th, amount=2)

    workers.update(0)

    from_cow = [t for t in workers._transport_queue if t.source is cow and t.resource == "hide"]  # noqa: SLF001
    assert len(from_cow) == 3


def test_demolish_cow_farm_drops_pending_hide_export_tasks() -> None:
    world = World(world_seed=0)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    world._iron.clear()  # noqa: SLF001
    world._gold.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    th = registry.place(TownHall, town_hall_origin_tile())
    cow = registry.place(CowFarm, near_town_hall_tile(19, 8))
    cow.construction_site = None
    cow.add_hide_out(1)
    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    workers.enqueue_transport_task(resource="hide", source=cow, target=th, amount=1)

    registry.demolish(cow, workers)

    assert not any(t.source is cow or t.target is cow for t in workers._transport_queue)  # noqa: SLF001
