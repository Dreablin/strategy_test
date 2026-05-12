"""Tests for generalized dining runtime with Canteen (T363)."""

from __future__ import annotations

from game.buildings.canteen import Canteen
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.canteen_dining import try_reserve_diner_slot_and_meal
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.worker_dining import (
    DINING_EAT_DURATION_MS,
    _try_start_eating,
    _worker_inside_building_footprint,
    update_dining_runtime,
)
from game.workers import WorkerManager
from game.world import World


def _setup():
    world = World(world_seed=0)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    world._iron.clear()  # noqa: SLF001
    world.refresh_passability_tile_caches()
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    canteen = registry.place(Canteen, near_town_hall_tile(5, 5))
    canteen.construction_site = None
    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    return world, registry, canteen, workers


def test_dining_requires_reservation_before_eating() -> None:
    world, registry, canteen, workers = _setup()
    canteen.add_local_storage("simple_meal", 1)
    baker = workers.hire("BAKER")
    assert baker is not None
    workers.reassign_all()
    assert not _try_start_eating(baker, canteen, 1000)


def test_dining_starts_after_reservation() -> None:
    world, registry, canteen, workers = _setup()
    canteen.add_local_storage("simple_meal", 1)
    baker = workers.hire("BAKER")
    assert baker is not None
    workers.reassign_all()
    assert try_reserve_diner_slot_and_meal(canteen, baker)
    assert _try_start_eating(baker, canteen, 1000)
    assert baker.state == "eating"


def test_dining_uses_meal_resource_key() -> None:
    world, registry, canteen, workers = _setup()
    assert canteen.meal_resource_key() == "simple_meal"
    canteen.add_local_storage("simple_meal", 1)
    baker = workers.hire("BAKER")
    assert baker is not None
    workers.reassign_all()
    try_reserve_diner_slot_and_meal(canteen, baker)
    _try_start_eating(baker, canteen, 0)
    assert canteen.local_storage_amount("simple_meal") == 0


def test_worker_inside_building_footprint() -> None:
    world, registry, canteen, workers = _setup()
    baker = workers.hire("BAKER")
    assert baker is not None
    workers.reassign_all()
    pos = canteen.grid_pos
    assert pos is not None
    baker.current_tile = pos
    assert _worker_inside_building_footprint(baker, canteen)
    baker.current_tile = (pos[0] + 10, pos[1] + 10)
    assert not _worker_inside_building_footprint(baker, canteen)


def test_eating_completes_after_duration() -> None:
    world, registry, canteen, workers = _setup()
    canteen.add_local_storage("simple_meal", 1)
    baker = workers.hire("BAKER")
    assert baker is not None
    workers.reassign_all()
    try_reserve_diner_slot_and_meal(canteen, baker)

    now_ms = 0
    for _ in range(500):
        now_ms += 100
        update_dining_runtime(
            baker, canteen=canteen, world=world,
            worker_manager=workers, registry=registry, now_ms=now_ms,
        )
        if baker.dining_phase == "eating":
            break
    assert baker.dining_phase == "eating"

    now_ms += DINING_EAT_DURATION_MS + 1
    update_dining_runtime(
        baker, canteen=canteen, world=world,
        worker_manager=workers, registry=registry, now_ms=now_ms,
    )
    assert baker.dining_phase in ("returning_to_work", "none")
