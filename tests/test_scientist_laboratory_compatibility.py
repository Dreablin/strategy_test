"""Scientist-to-Laboratory compatibility tests (T402)."""

from __future__ import annotations

from game.buildings.laboratory import Laboratory
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.worker_hiring import WORKER_TO_BUILDING, worker_compatible_building_types
from game.workers import WorkerManager
from game.world import World


def test_scientist_maps_to_laboratory_in_worker_to_building() -> None:
    assert WORKER_TO_BUILDING["SCIENTIST"] == "LABORATORY"


def test_scientist_compatible_with_laboratory() -> None:
    compatible = worker_compatible_building_types("SCIENTIST")
    assert compatible == frozenset({"LABORATORY"})


def test_scientist_not_compatible_with_other_buildings() -> None:
    compatible = worker_compatible_building_types("SCIENTIST")
    assert "WINERY" not in compatible
    assert "BAKERY" not in compatible
    assert "SCHOOL" not in compatible


def test_scientist_auto_assigned_to_built_laboratory() -> None:
    world = World(world_seed=0)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    world._iron.clear()  # noqa: SLF001
    world.refresh_passability_tile_caches()
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    laboratory = registry.place(Laboratory, near_town_hall_tile(10, 10))
    laboratory.construction_site = None

    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    scientist = workers.hire("SCIENTIST")
    assert scientist is not None

    workers.reassign_all()
    assert scientist.assigned_building is laboratory


def test_other_workers_not_assigned_to_laboratory() -> None:
    world = World(world_seed=0)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    world._iron.clear()  # noqa: SLF001
    world.refresh_passability_tile_caches()
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    laboratory = registry.place(Laboratory, near_town_hall_tile(10, 10))
    laboratory.construction_site = None

    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    carrier = workers.hire("CARRIER")
    assert carrier is not None

    workers.reassign_all()
    assert carrier.assigned_building is not laboratory
