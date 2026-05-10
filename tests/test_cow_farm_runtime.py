"""Cow Farm processor: herder cycles, recipe, and gates."""

from __future__ import annotations

from game.buildings.cow_farm import CowFarm
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.config import building_int_setting, near_town_hall_tile, town_hall_origin_tile
from game.construction import ConstructionSite
from game.world import World
from game.worker_models import Worker
from game.workers import WorkerManager, building_center_tile


def test_cow_farm_requires_full_recipe_to_start_processing() -> None:
    world = World(world_seed=0)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    world._iron.clear()  # noqa: SLF001
    world._gold.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    farm = registry.place(CowFarm, near_town_hall_tile(19, 8))
    farm.construction_site = None
    farm.add_wheat_in(2)
    farm.add_water_in(3)
    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    herder = Worker("ANIMAL_HERDER")
    workers.add_worker(herder)
    workers.assign_to_building(herder, farm)
    herder.current_tile = building_center_tile(farm)
    herder.stand_tile = herder.current_tile
    herder.state = "working"

    workers.update(5_000)

    assert herder.state == "working"
    assert farm.processing_started_ms == 0


def test_animal_herder_processes_cow_farm_recipe_and_rests() -> None:
    world = World(world_seed=0)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    world._iron.clear()  # noqa: SLF001
    world._gold.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    farm = registry.place(CowFarm, near_town_hall_tile(19, 8))
    farm.construction_site = None
    w_req = farm.recipe_wheat_required()
    water_req = farm.recipe_water_required()
    farm.add_wheat_in(w_req)
    farm.add_water_in(water_req)
    cycle_ms = building_int_setting("COW_FARM", "production", "cycle_ms")
    rest_ms = building_int_setting("COW_FARM", "production", "rest_ms")
    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    herder = Worker("ANIMAL_HERDER")
    workers.add_worker(herder)
    workers.assign_to_building(herder, farm)
    herder.current_tile = building_center_tile(farm)
    herder.stand_tile = herder.current_tile
    herder.state = "working"

    workers.update(1_000)
    assert herder.state == "processing"
    assert farm.processing_started_ms == 1_000

    workers.update(1_000 + cycle_ms)
    assert farm.wheat_amount() == 0
    assert farm.water_amount() == 0
    assert farm.beef_amount() == farm.recipe_beef_output()
    assert farm.hide_amount() == farm.recipe_hide_output()
    assert farm.processing_started_ms == 0
    assert herder.state == "resting"
    assert herder.camp_wait_until_ms == 1_000 + cycle_ms + rest_ms


def test_cow_farm_inactive_does_not_start_processing() -> None:
    world = World(world_seed=0)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    world._iron.clear()  # noqa: SLF001
    world._gold.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    farm = registry.place(CowFarm, near_town_hall_tile(19, 8))
    farm.construction_site = None
    farm.add_wheat_in(farm.recipe_wheat_required())
    farm.add_water_in(farm.recipe_water_required())
    farm.set_active(False)
    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    herder = Worker("ANIMAL_HERDER")
    workers.add_worker(herder)
    workers.assign_to_building(herder, farm)
    herder.current_tile = building_center_tile(farm)
    herder.stand_tile = herder.current_tile
    herder.state = "working"

    workers.update(5_000)

    assert farm.processing_started_ms == 0
    assert herder.state == "resting"


def test_cow_farm_full_outputs_block_new_cycle() -> None:
    world = World(world_seed=0)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    world._iron.clear()  # noqa: SLF001
    world._gold.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    farm = registry.place(CowFarm, near_town_hall_tile(19, 8))
    farm.construction_site = None
    farm.add_beef_out(farm.beef_capacity())
    farm.add_hide_out(farm.hide_capacity())
    farm.add_wheat_in(farm.recipe_wheat_required())
    farm.add_water_in(farm.recipe_water_required())
    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    herder = Worker("ANIMAL_HERDER")
    workers.add_worker(herder)
    workers.assign_to_building(herder, farm)
    herder.current_tile = building_center_tile(farm)
    herder.stand_tile = herder.current_tile
    herder.state = "working"

    workers.update(5_000)

    assert farm.processing_started_ms == 0
    assert herder.state == "working"


def test_cow_farm_under_construction_skips_processor() -> None:
    world = World(world_seed=0)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    world._iron.clear()  # noqa: SLF001
    world._gold.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    farm = registry.place(CowFarm, near_town_hall_tile(19, 8))
    farm.construction_site = ConstructionSite(
        required_resources={},
        delivered_resources={},
        build_time_ms=60_000,
        build_started_ms=None,
        builder=None,
        target_level=1,
    )
    farm.add_wheat_in(farm.recipe_wheat_required())
    farm.add_water_in(farm.recipe_water_required())
    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    herder = Worker("ANIMAL_HERDER")
    workers.add_worker(herder)
    workers.assign_to_building(herder, farm)
    herder.current_tile = building_center_tile(farm)
    herder.stand_tile = herder.current_tile
    herder.state = "working"

    workers.update(5_000)

    assert farm.processing_started_ms == 0
