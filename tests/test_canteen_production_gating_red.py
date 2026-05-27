"""Canteen cook production gating (T254 / T255).

Validates gating aligned with other processors: no cook, inactive building,
missing inputs, full `simple_meal` storage, and inactive mid-cycle completion.
"""

from __future__ import annotations

from game.buildings.canteen import Canteen
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.world import World
from game.worker_models import Worker
from game.workers import WorkerManager, building_center_tile


def _registry_with_canteen() -> tuple[World, BuildingRegistry, Canteen]:
    world = World(world_seed=0)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    canteen = registry.place(Canteen, near_town_hall_tile(14, 8))
    canteen.construction_site = None
    return world, registry, canteen


def _cook_ready_at_canteen(wm: WorkerManager, canteen: Canteen) -> Worker:
    cook = Worker("COOK")
    wm.add_worker(cook)
    wm.assign_to_building(cook, canteen)
    center = building_center_tile(canteen)
    cook.current_tile = center
    cook.stand_tile = center
    cook.state = "working"
    return cook


def test_no_assigned_cook_means_no_canteen_production_start() -> None:
    _, registry, canteen = _registry_with_canteen()
    canteen.add_local_storage("chicken", 1)
    canteen.add_local_storage("bread", 1)
    canteen.add_local_storage("water", 1)
    wm = WorkerManager(registry, now_ms_fn=lambda: 0)

    wm.update(1_000)

    assert canteen.processing_started_ms == 0
    assert canteen.local_storage_amount("simple_meal") == 0
    assert canteen.local_storage_amount("chicken") == 1


def test_inactive_canteen_does_not_start_new_production_cycle() -> None:
    _, registry, canteen = _registry_with_canteen()
    canteen.add_local_storage("chicken", 1)
    canteen.add_local_storage("bread", 1)
    canteen.add_local_storage("water", 1)
    canteen.set_active(False)
    wm = WorkerManager(registry, now_ms_fn=lambda: 0)
    _cook_ready_at_canteen(wm, canteen)

    wm.update(1_000)

    assert canteen.processing_started_ms == 0
    assert canteen.local_storage_amount("simple_meal") == 0


def test_canteen_missing_chicken_blocks_cycle_start() -> None:
    _, registry, canteen = _registry_with_canteen()
    canteen.add_local_storage("bread", 1)
    canteen.add_local_storage("water", 1)
    wm = WorkerManager(registry, now_ms_fn=lambda: 0)
    _cook_ready_at_canteen(wm, canteen)

    wm.update(1_000)

    assert canteen.processing_started_ms == 0


def test_canteen_missing_bread_blocks_cycle_start() -> None:
    _, registry, canteen = _registry_with_canteen()
    canteen.add_local_storage("chicken", 1)
    canteen.add_local_storage("water", 1)
    wm = WorkerManager(registry, now_ms_fn=lambda: 0)
    _cook_ready_at_canteen(wm, canteen)

    wm.update(1_000)

    assert canteen.processing_started_ms == 0


def test_canteen_missing_water_blocks_cycle_start() -> None:
    _, registry, canteen = _registry_with_canteen()
    canteen.add_local_storage("chicken", 1)
    canteen.add_local_storage("bread", 1)
    wm = WorkerManager(registry, now_ms_fn=lambda: 0)
    _cook_ready_at_canteen(wm, canteen)

    wm.update(1_000)

    assert canteen.processing_started_ms == 0


def test_full_simple_meal_local_storage_blocks_new_cycle() -> None:
    _, registry, canteen = _registry_with_canteen()
    cap = canteen.local_storage_capacity("simple_meal")
    canteen.add_local_storage("simple_meal", cap)
    canteen.add_local_storage("chicken", 1)
    canteen.add_local_storage("bread", 1)
    canteen.add_local_storage("water", 1)
    wm = WorkerManager(registry, now_ms_fn=lambda: 0)
    _cook_ready_at_canteen(wm, canteen)

    wm.update(1_000)

    assert canteen.processing_started_ms == 0
    assert canteen.local_storage_amount("simple_meal") == cap


def test_inactive_mid_cycle_finishes_current_then_blocks_next_like_other_processors() -> None:
    """Match sawmill/bakery: in-flight cycle completes; no new cycle while inactive."""
    _, registry, canteen = _registry_with_canteen()
    canteen.add_local_storage("chicken", 2)
    canteen.add_local_storage("bread", 2)
    canteen.add_local_storage("water", 2)
    wm = WorkerManager(registry, now_ms_fn=lambda: 0)
    cook = _cook_ready_at_canteen(wm, canteen)

    t0 = 1_000
    wm.update(t0)
    assert cook.state == "processing"
    assert canteen.processing_started_ms == t0

    canteen.set_active(False)

    t_done = t0 + canteen.processing_duration_ms
    wm.update(t_done)
    assert canteen.local_storage_amount("simple_meal") == 1
    assert canteen.local_storage_amount("chicken") == 1
    assert canteen.local_storage_amount("bread") == 1
    assert canteen.local_storage_amount("water") == 1
    assert canteen.processing_started_ms == 0
    assert cook.state == "resting"

    t_after_rest = cook.camp_wait_until_ms + 1
    wm.update(t_after_rest)
    assert canteen.processing_started_ms == 0
    assert canteen.local_storage_amount("simple_meal") == 1

    wm.update(t_after_rest + 60_000)
    assert canteen.processing_started_ms == 0
    assert canteen.local_storage_amount("simple_meal") == 1
