"""Cow Farm water refill from wells (generic water_input_transport_tasks)."""

from __future__ import annotations

from game.buildings.bakery import Bakery
from game.buildings.chicken_farm import ChickenFarm
from game.buildings.cow_farm import CowFarm
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.buildings.well import Well
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.transport_tasks import water_input_transport_tasks
from game.world import World
from game.workers import WorkerManager


def _registry_with_th() -> tuple[BuildingRegistry, TownHall]:
    world = World(world_seed=0)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    world._iron.clear()  # noqa: SLF001
    world._gold.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    th = registry.place(TownHall, town_hall_origin_tile())
    return registry, th


def _fill_well(well: Well) -> None:
    """Level-1 wells only hold one unit of water."""
    well.add_water_in(well.water_capacity())


def _place_stocked_wells(registry: BuildingRegistry, positions: list[tuple[int, int]]) -> list[Well]:
    out: list[Well] = []
    for pos in positions:
        w = registry.place(Well, near_town_hall_tile(*pos))
        w.construction_site = None
        _fill_well(w)
        out.append(w)
    return out


def test_water_input_tasks_plan_well_to_cow_farm_refill() -> None:
    registry, _ = _registry_with_th()
    cow = registry.place(CowFarm, near_town_hall_tile(20, 8))
    cow.construction_site = None
    cap = cow.water_capacity()
    # Chebyshev spacing ≥2 between 2×2 footprints ⇒ well origins ≥3 tiles apart on X.
    wells = _place_stocked_wells(registry, [(24, 8), (27, 8), (30, 8)])
    assert cow.water_amount() == 0

    tasks = water_input_transport_tasks(registry)
    to_cow = [t for t in tasks if t.target is cow and t.resource == "water" and t.source in wells]

    assert len(to_cow) == cap


def test_water_input_tasks_respect_inbound_for_cow_farm() -> None:
    registry, _ = _registry_with_th()
    cow = registry.place(CowFarm, near_town_hall_tile(20, 8))
    cow.construction_site = None
    _place_stocked_wells(registry, [(24, 8)])
    cap = cow.water_capacity()
    inbound = {id(cow): cap - 1}

    tasks = water_input_transport_tasks(registry, inbound_water_by_target_id=inbound)
    to_cow = [t for t in tasks if t.target is cow and t.resource == "water"]

    assert len(to_cow) == 1


def test_cow_farm_water_enqueue_respects_queued_inbound() -> None:
    registry, _ = _registry_with_th()
    cow = registry.place(CowFarm, near_town_hall_tile(20, 8))
    cow.construction_site = None
    wells = _place_stocked_wells(registry, [(24, 8), (27, 8), (30, 8), (33, 8)])
    well0 = wells[0]
    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    workers.enqueue_transport_task(resource="water", source=well0, target=cow, amount=2)

    workers.update(0)

    to_cow = [t for t in workers._transport_queue if t.target is cow and t.resource == "water"]  # noqa: SLF001
    assert len(to_cow) == cow.water_capacity()


def test_water_plans_include_cow_farm_and_bakery_when_both_need_water() -> None:
    """Regression: Cow Farm must not crowd out existing bakery water planning."""
    registry, _ = _registry_with_th()
    bakery = registry.place(Bakery, near_town_hall_tile(18, 8))
    cow = registry.place(CowFarm, near_town_hall_tile(22, 8))
    for b in (bakery, cow):
        b.construction_site = None
    # Bakery needs 1 top-up; cow needs full cap — four level-1 wells (1 water each).
    _place_stocked_wells(registry, [(27, 8), (30, 8), (33, 8), (36, 8)])
    bakery.add_water_in(max(0, bakery.water_capacity() - 1))

    tasks = water_input_transport_tasks(registry)
    assert any(t.target is cow and t.resource == "water" for t in tasks)
    assert any(t.target is bakery and t.resource == "water" for t in tasks)


def test_water_plans_include_cow_farm_and_chicken_farm() -> None:
    registry, _ = _registry_with_th()
    chicken = registry.place(ChickenFarm, near_town_hall_tile(16, 8))
    cow = registry.place(CowFarm, near_town_hall_tile(22, 8))
    for b in (chicken, cow):
        b.construction_site = None
    _place_stocked_wells(registry, [(27, 8), (30, 8), (33, 8), (36, 8)])
    chicken.add_water_in(max(0, chicken.water_capacity() - 1))
    cow.add_water_in(max(0, cow.water_capacity() - 1))

    tasks = water_input_transport_tasks(registry)
    assert any(t.target is chicken and t.resource == "water" for t in tasks)
    assert any(t.target is cow and t.resource == "water" for t in tasks)
