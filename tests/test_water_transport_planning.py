"""Water delivery planning from well storage (T281)."""

from __future__ import annotations

from game.buildings.bakery import Bakery
from game.buildings.canteen import Canteen
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.buildings.well import Well
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.transport_tasks import water_input_transport_tasks
from game.world import World


def _registry_with_th() -> tuple[BuildingRegistry, TownHall]:
    world = World(world_seed=0)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    th = registry.place(TownHall, town_hall_origin_tile())
    return registry, th


def test_water_tasks_pick_nearest_stocked_well_per_consumer() -> None:
    registry, _ = _registry_with_th()
    well_far = registry.place(Well, near_town_hall_tile(7, 8))
    well_near = registry.place(Well, near_town_hall_tile(24, 8))
    bakery = registry.place(Bakery, near_town_hall_tile(20, 8))
    for b in (well_far, well_near, bakery):
        b.construction_site = None
    bakery.add_water_in(max(0, bakery.water_capacity() - 1))
    well_far.add_water_in(1)
    well_near.add_water_in(1)

    tasks = water_input_transport_tasks(registry)
    water_tasks = [t for t in tasks if t.resource == "water" and t.target is bakery]
    assert water_tasks
    assert all(t.source is well_near for t in water_tasks)


def test_later_bakery_gets_water_when_second_well_is_stocked() -> None:
    """Regression: a farther bakery must not starve when a nearer well serves a closer bakery."""
    registry, _ = _registry_with_th()
    well_a = registry.place(Well, near_town_hall_tile(8, 10))
    well_b = registry.place(Well, near_town_hall_tile(26, 10))
    bakery_early = registry.place(Bakery, near_town_hall_tile(10, 10))
    bakery_late = registry.place(Bakery, near_town_hall_tile(22, 10))
    for b in (well_a, well_b, bakery_early, bakery_late):
        b.construction_site = None
    bakery_early.add_water_in(max(0, bakery_early.water_capacity() - 1))
    bakery_late.add_water_in(max(0, bakery_late.water_capacity() - 1))
    well_a.add_water_in(1)
    well_b.add_water_in(1)

    tasks = water_input_transport_tasks(registry)
    to_late = [t for t in tasks if t.target is bakery_late and t.resource == "water"]
    assert to_late, "second bakery must receive planned water deliveries"
    assert any(t.source is well_b for t in to_late)


def test_water_tasks_second_consumer_prefers_canteen_nearest_well() -> None:
    registry, _ = _registry_with_th()
    w_left = registry.place(Well, near_town_hall_tile(8, 12))
    w_right = registry.place(Well, near_town_hall_tile(26, 12))
    cant_left = registry.place(Canteen, near_town_hall_tile(10, 12))
    cant_right = registry.place(Canteen, near_town_hall_tile(20, 12))
    for b in (w_left, w_right, cant_left, cant_right):
        b.construction_site = None
    cap_w = cant_right.local_storage_capacity("water")
    cant_left.add_local_storage("water", max(0, cap_w - 1))
    cant_right.add_local_storage("water", max(0, cap_w - 1))
    w_left.add_water_in(1)
    w_right.add_water_in(1)

    tasks = water_input_transport_tasks(registry)
    to_right = [t for t in tasks if t.target is cant_right and t.resource == "water"]
    assert to_right
    assert all(t.source is w_right for t in to_right)


def test_inbound_dict_prevents_overfilling_consumer() -> None:
    registry, _ = _registry_with_th()
    well = registry.place(Well, near_town_hall_tile(20, 8))
    bakery = registry.place(Bakery, near_town_hall_tile(14, 8))
    well.construction_site = None
    bakery.construction_site = None
    well.add_water_in(1)
    cap = bakery.water_capacity()
    inbound = {id(bakery): cap}

    tasks = water_input_transport_tasks(registry, inbound_water_by_target_id=inbound)
    assert [t for t in tasks if t.target is bakery] == []
