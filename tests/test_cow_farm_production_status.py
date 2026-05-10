"""Cow Farm integration with ``production_status_for_building``."""

from __future__ import annotations

from game.buildings.cow_farm import CowFarm
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.world import World
from game.worker_models import Worker
from game.worker_status import production_status_for_building
from game.workers import WorkerManager, building_center_tile


def _registry_with_cow_farm() -> tuple[BuildingRegistry, CowFarm]:
    world = World(world_seed=0)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    world._iron.clear()  # noqa: SLF001
    world._gold.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    farm = registry.place(CowFarm, near_town_hall_tile(19, 8))
    farm.construction_site = None
    return registry, farm


def test_cow_farm_production_status_no_worker() -> None:
    registry, farm = _registry_with_cow_farm()
    mgr = WorkerManager(registry, now_ms_fn=lambda: 0)
    assert production_status_for_building(mgr, farm) == "No worker"


def test_cow_farm_production_status_inactive() -> None:
    registry, farm = _registry_with_cow_farm()
    farm.add_wheat_in(farm.recipe_wheat_required())
    farm.add_water_in(farm.recipe_water_required())
    farm.set_active(False)
    mgr = WorkerManager(registry, now_ms_fn=lambda: 0)
    herder = Worker("ANIMAL_HERDER")
    mgr.add_worker(herder)
    mgr.assign_to_building(herder, farm)
    assert production_status_for_building(mgr, farm) == "Inactive"


def test_cow_farm_production_status_resting() -> None:
    registry, farm = _registry_with_cow_farm()
    farm.add_wheat_in(farm.recipe_wheat_required())
    farm.add_water_in(farm.recipe_water_required())
    mgr = WorkerManager(registry, now_ms_fn=lambda: 0)
    herder = Worker("ANIMAL_HERDER")
    mgr.add_worker(herder)
    mgr.assign_to_building(herder, farm)
    herder.state = "resting"
    assert production_status_for_building(mgr, farm) == "Resting"


def test_cow_farm_production_status_output_full() -> None:
    registry, farm = _registry_with_cow_farm()
    farm.add_beef_out(farm.beef_capacity())
    farm.add_hide_out(farm.hide_capacity())
    farm.add_wheat_in(farm.recipe_wheat_required())
    farm.add_water_in(farm.recipe_water_required())
    mgr = WorkerManager(registry, now_ms_fn=lambda: 0)
    herder = Worker("ANIMAL_HERDER")
    mgr.add_worker(herder)
    mgr.assign_to_building(herder, farm)
    assert production_status_for_building(mgr, farm) == "Output full"


def test_cow_farm_production_status_no_wheat() -> None:
    registry, farm = _registry_with_cow_farm()
    farm.add_water_in(farm.recipe_water_required())
    mgr = WorkerManager(registry, now_ms_fn=lambda: 0)
    herder = Worker("ANIMAL_HERDER")
    mgr.add_worker(herder)
    mgr.assign_to_building(herder, farm)
    assert production_status_for_building(mgr, farm) == "No wheat"


def test_cow_farm_production_status_no_water() -> None:
    registry, farm = _registry_with_cow_farm()
    farm.add_wheat_in(farm.recipe_wheat_required())
    mgr = WorkerManager(registry, now_ms_fn=lambda: 0)
    herder = Worker("ANIMAL_HERDER")
    mgr.add_worker(herder)
    mgr.assign_to_building(herder, farm)
    assert production_status_for_building(mgr, farm) == "No water"


def test_cow_farm_production_status_processing() -> None:
    registry, farm = _registry_with_cow_farm()
    farm.add_wheat_in(farm.recipe_wheat_required())
    farm.add_water_in(farm.recipe_water_required())
    mgr = WorkerManager(registry, now_ms_fn=lambda: 0)
    herder = Worker("ANIMAL_HERDER")
    mgr.add_worker(herder)
    mgr.assign_to_building(herder, farm)
    herder.current_tile = building_center_tile(farm)
    herder.state = "processing"
    assert production_status_for_building(mgr, farm) == "Processing"


def test_cow_farm_production_status_ready() -> None:
    registry, farm = _registry_with_cow_farm()
    farm.add_wheat_in(farm.recipe_wheat_required())
    farm.add_water_in(farm.recipe_water_required())
    mgr = WorkerManager(registry, now_ms_fn=lambda: 0)
    herder = Worker("ANIMAL_HERDER")
    mgr.add_worker(herder)
    mgr.assign_to_building(herder, farm)
    herder.state = "working"
    assert production_status_for_building(mgr, farm) == "Ready"
