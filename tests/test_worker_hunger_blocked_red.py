"""T271 RED: throttled hunger when starting a new cycle is blocked (T272 implements API + wiring)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from game.buildings.bakery import Bakery
from game.buildings.canteen import Canteen
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.worker_hunger import (
    BLOCKED_HUNGER_RETRY_MS,
    try_blocked_cycle_hunger_check,
)
from game.worker_models import Worker
from game.world import World
from game.workers import WorkerManager


def _scene_with_canteen() -> tuple[World, BuildingRegistry, WorkerManager, Canteen, Bakery, Worker]:
    world = World(world_seed=31)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    world.refresh_passability_tile_caches()
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    for b in registry.all():
        if b.type_tag == "TOWN_HALL":
            b.level = 5
            break
    canteen = registry.place(Canteen, (52, 50))
    canteen.construction_site = None
    bakery = registry.place(Bakery, near_town_hall_tile(6, 4))
    bakery.construction_site = None
    bakery.flour_in = 0
    bakery.water_in = 0
    wm = WorkerManager(registry)
    worker = Worker("BAKER", stand_tile=(46, 50))
    worker.current_tile = worker.stand_tile
    worker.assigned_building = bakery
    worker.state = "working"
    worker.idle = False
    worker.satiety = 400
    worker.blocked_cycle_hunger_try_ms = -1
    return world, registry, wm, canteen, bakery, worker


@patch("game.canteen_selection.reserve_nearest_reachable_canteen_if_hungry")
def test_not_hungry_blocked_cycle_does_not_touch_reserve(mock_reserve: MagicMock) -> None:
    world, registry, wm, _, _, worker = _scene_with_canteen()
    worker.satiety = 8_000
    assert not try_blocked_cycle_hunger_check(
        worker,
        world=world,
        registry=registry,
        worker_manager=wm,
        now_ms=50_000,
    )
    mock_reserve.assert_not_called()
    assert worker.blocked_cycle_hunger_try_ms == -1


@patch("game.canteen_selection.reserve_nearest_reachable_canteen_if_hungry")
def test_hungry_blocked_cycle_first_attempt_calls_reserve(mock_reserve: MagicMock) -> None:
    world, registry, wm, canteen, _, worker = _scene_with_canteen()
    mock_reserve.return_value = canteen
    assert try_blocked_cycle_hunger_check(
        worker,
        world=world,
        registry=registry,
        worker_manager=wm,
        now_ms=60_000,
    )
    assert mock_reserve.call_count == 1


@patch("game.canteen_selection.reserve_nearest_reachable_canteen_if_hungry")
def test_hungry_blocked_cycle_second_tick_within_interval_does_not_spam_reserve(
    mock_reserve: MagicMock,
) -> None:
    world, registry, wm, canteen, _, worker = _scene_with_canteen()
    mock_reserve.return_value = canteen
    t0 = 100_000
    assert try_blocked_cycle_hunger_check(
        worker,
        world=world,
        registry=registry,
        worker_manager=wm,
        now_ms=t0,
    )
    assert mock_reserve.call_count == 1
    assert not try_blocked_cycle_hunger_check(
        worker,
        world=world,
        registry=registry,
        worker_manager=wm,
        now_ms=t0 + min(1_000, BLOCKED_HUNGER_RETRY_MS // 2),
    )
    assert mock_reserve.call_count == 1


@patch("game.canteen_selection.reserve_nearest_reachable_canteen_if_hungry")
def test_hungry_blocked_cycle_after_retry_interval_may_call_reserve_again(
    mock_reserve: MagicMock,
) -> None:
    world, registry, wm, _, _, worker = _scene_with_canteen()
    mock_reserve.return_value = None
    t0 = 200_000
    assert not try_blocked_cycle_hunger_check(
        worker,
        world=world,
        registry=registry,
        worker_manager=wm,
        now_ms=t0,
    )
    assert mock_reserve.call_count == 1
    assert not try_blocked_cycle_hunger_check(
        worker,
        world=world,
        registry=registry,
        worker_manager=wm,
        now_ms=t0 + BLOCKED_HUNGER_RETRY_MS - 1,
    )
    assert mock_reserve.call_count == 1
    worker.dining_canteen = None
    mock_reserve.return_value = None
    assert not try_blocked_cycle_hunger_check(
        worker,
        world=world,
        registry=registry,
        worker_manager=wm,
        now_ms=t0 + BLOCKED_HUNGER_RETRY_MS,
    )
    assert mock_reserve.call_count == 2


def test_blocked_hunger_retry_interval_is_sane() -> None:
    assert BLOCKED_HUNGER_RETRY_MS >= 1_000
    assert BLOCKED_HUNGER_RETRY_MS <= 120_000
