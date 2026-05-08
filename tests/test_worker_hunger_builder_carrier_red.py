"""T273 RED: builder/carrier hunger hooks around idle and post-completion moments."""

from __future__ import annotations

from game.buildings.canteen import Canteen
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.worker_hunger import (
    try_builder_hunger_after_completion_or_idle,
    try_carrier_hunger_after_delivery_or_idle,
)
from game.worker_models import Worker
from game.world import World
from game.workers import WorkerManager


def _base() -> tuple[World, BuildingRegistry, WorkerManager, Canteen]:
    world = World(world_seed=41)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    world.refresh_passability_tile_caches()
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    for b in registry.all():
        if b.type_tag == "TOWN_HALL":
            b.level = 5
            break
    canteen = registry.place(Canteen, near_town_hall_tile(10, 4))
    canteen.construction_site = None
    return world, registry, WorkerManager(registry), canteen


def test_builder_idle_without_assigned_construction_attempts_hunger() -> None:
    world, registry, wm, canteen = _base()
    builder = Worker("BUILDER", stand_tile=near_town_hall_tile(4, 8))
    builder.current_tile = builder.stand_tile
    builder.state = "idle"
    builder.idle = True
    builder.assigned_building = None
    builder.satiety = 400

    assert try_builder_hunger_after_completion_or_idle(
        builder,
        world=world,
        registry=registry,
        worker_manager=wm,
        now_ms=12_000,
    )
    assert builder.dining_canteen is canteen


def test_builder_active_construction_is_not_diverted_to_canteen() -> None:
    world, registry, wm, _ = _base()
    builder = Worker("BUILDER", stand_tile=near_town_hall_tile(4, 8))
    builder.current_tile = builder.stand_tile
    builder.state = "building"
    builder.idle = False
    builder.satiety = 300

    assert not try_builder_hunger_after_completion_or_idle(
        builder,
        world=world,
        registry=registry,
        worker_manager=wm,
        now_ms=13_000,
    )
    assert builder.state == "building"
    assert builder.dining_canteen is None


def test_carrier_idle_without_task_attempts_hunger() -> None:
    world, registry, wm, canteen = _base()
    carrier = Worker("CARRIER", stand_tile=near_town_hall_tile(6, 8))
    carrier.current_tile = carrier.stand_tile
    carrier.state = "idle"
    carrier.idle = True
    carrier.transport_task = None
    carrier.carrying = None
    carrier.satiety = 500

    assert try_carrier_hunger_after_delivery_or_idle(
        carrier,
        world=world,
        registry=registry,
        worker_manager=wm,
        now_ms=14_000,
    )
    assert carrier.dining_canteen is canteen


def test_carrier_with_active_cargo_is_not_diverted_to_canteen() -> None:
    world, registry, wm, _ = _base()
    carrier = Worker("CARRIER", stand_tile=near_town_hall_tile(6, 8))
    carrier.current_tile = carrier.stand_tile
    carrier.state = "moving"
    carrier.idle = False
    carrier.carrying = "wood"
    carrier.satiety = 250

    assert not try_carrier_hunger_after_delivery_or_idle(
        carrier,
        world=world,
        registry=registry,
        worker_manager=wm,
        now_ms=15_000,
    )
    assert carrier.carrying == "wood"
    assert carrier.dining_canteen is None
