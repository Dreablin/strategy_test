"""ANIMAL_HERDER may staff CHICKEN_FARM and COW_FARM (auto-assignment)."""

from __future__ import annotations

from game.buildings.chicken_farm import ChickenFarm
from game.buildings.cow_farm import CowFarm
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.world import World
from game.worker_hiring import worker_compatible_building_types
from game.worker_models import Worker
from game.workers import WorkerManager


def test_worker_compatible_building_types_herder_includes_cow_and_chicken() -> None:
    assert worker_compatible_building_types("ANIMAL_HERDER") == frozenset({"CHICKEN_FARM", "COW_FARM"})
    assert worker_compatible_building_types("MILLER") == frozenset({"MILL"})


def test_animal_herder_reassigns_to_chicken_farm_when_present() -> None:
    world = World(world_seed=0)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    world._iron.clear()  # noqa: SLF001
    world._gold.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    farm = registry.place(ChickenFarm, near_town_hall_tile(14, 8))
    farm.construction_site = None
    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    herder = Worker("ANIMAL_HERDER")
    workers.add_worker(herder)

    workers.reassign_all()

    assert herder.assigned_building is farm


def test_animal_herder_reassigns_to_cow_farm_when_no_chicken_farm() -> None:
    world = World(world_seed=0)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    world._iron.clear()  # noqa: SLF001
    world._gold.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    cow = registry.place(CowFarm, near_town_hall_tile(16, 8))
    cow.construction_site = None
    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    herder = Worker("ANIMAL_HERDER")
    workers.add_worker(herder)

    workers.reassign_all()

    assert herder.assigned_building is cow


def test_animal_herder_reassigns_to_cow_when_chicken_already_staffed() -> None:
    world = World(world_seed=0)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    world._iron.clear()  # noqa: SLF001
    world._gold.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    chicken = registry.place(ChickenFarm, near_town_hall_tile(14, 8))
    chicken.construction_site = None
    cow = registry.place(CowFarm, near_town_hall_tile(22, 8))
    cow.construction_site = None
    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    first = Worker("ANIMAL_HERDER")
    second = Worker("ANIMAL_HERDER")
    workers.add_worker(first)
    workers.add_worker(second)
    workers.assign_to_building(first, chicken)

    workers.reassign_all()

    assert first.assigned_building is chicken
    assert second.assigned_building is cow
