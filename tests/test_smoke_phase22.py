"""Phase 22 smoke: canteen inputs, cook meal production, hunger reservation, wait, eat, release."""

from __future__ import annotations

from game.buildings.bakery import Bakery
from game.buildings.canteen import Canteen
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.buildings.well import Well
from game.canteen_dining import count_reserved_diner_slots
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.worker_dining import (
    DINING_EAT_DURATION_MS,
    dining_runtime_phase,
    update_dining_runtime,
)
from game.worker_hunger import try_carrier_hunger_after_delivery_or_idle
from game.worker_models import Worker
from game.worker_satiety import MAX_WORKER_SATIETY
from game.world import World
from game.workers import WorkerManager


def _advance_until(
    workers: WorkerManager,
    now_ms: dict[str, int],
    predicate,
    *,
    step_ms: int = 500,
    steps: int = 4000,
) -> bool:
    for _ in range(steps):
        now_ms["t"] += step_ms
        workers.reassign_all()
        workers.update(now_ms["t"])
        if predicate():
            return True
    return False


def test_smoke_phase22_canteen_meal_and_dining_end_to_end() -> None:
    now_ms = {"t": 0}
    world = World(world_seed=22)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    town_hall.level = 5
    canteen = registry.place(Canteen, near_town_hall_tile(14, 8))
    canteen.construction_site = None
    bakery = registry.place(Bakery, near_town_hall_tile(8, 8))
    bakery.construction_site = None
    well = registry.place(Well, near_town_hall_tile(10, 12))
    well.construction_site = None
    town_hall.add_to_warehouse("chicken", 2)
    town_hall.add_to_warehouse("bread", 2)

    workers = WorkerManager(registry, now_ms_fn=lambda: now_ms["t"])
    carrier_a = workers.hire("CARRIER")
    carrier_b = workers.hire("CARRIER")
    cook = workers.hire("COOK")
    assert carrier_a is not None
    assert carrier_b is not None
    assert cook is not None
    workers.reassign_all()
    assigned_cook = _advance_until(
        workers,
        now_ms,
        lambda: any(w.type_tag == "COOK" and w.assigned_building is canteen for w in workers.workers()),
        steps=1200,
    )
    assert assigned_cook, "expected cook assigned to canteen"

    delivered_inputs = _advance_until(
        workers,
        now_ms,
        lambda: (
            canteen.local_storage_amount("chicken") >= 1
            and canteen.local_storage_amount("bread") >= 1
            and canteen.local_storage_amount("water") >= 1
        ),
        steps=3000,
    )
    assert delivered_inputs, "expected chicken/bread/water delivered to canteen"

    produced_meal = _advance_until(
        workers,
        now_ms,
        lambda: canteen.local_storage_amount("simple_meal") >= 1,
        steps=5000,
    )
    assert produced_meal, "expected cook to produce at least one simple_meal"

    diner = Worker("CARRIER", stand_tile=near_town_hall_tile(6, 10))
    diner.current_tile = diner.stand_tile
    diner.satiety = 300
    diner.state = "idle"
    diner.idle = True

    reserved = try_carrier_hunger_after_delivery_or_idle(
        diner,
        world=world,
        registry=registry,
        worker_manager=workers,
        now_ms=now_ms["t"],
    )
    assert reserved, "expected hungry carrier to reserve a canteen diner slot"
    assert diner.dining_meal_reserved is True
    assert count_reserved_diner_slots(canteen) >= 1
    assert canteen.local_storage_amount("simple_meal") >= 1

    eating = False
    for _ in range(1000):
        now_ms["t"] += 250
        update_dining_runtime(
            diner,
            canteen=canteen,
            world=world,
            worker_manager=workers,
            registry=registry,
            now_ms=now_ms["t"],
        )
        if dining_runtime_phase(diner) == "eating":
            eating = True
            break
    assert eating, "expected diner to start eating after reaching canteen with reserved meal"
    assert dining_runtime_phase(diner) == "eating"

    ate_done = _advance_until(
        workers,
        now_ms,
        lambda: (
            update_dining_runtime(
                diner,
                canteen=canteen,
                world=world,
                worker_manager=workers,
                registry=registry,
                now_ms=now_ms["t"],
            )
            or dining_runtime_phase(diner) == "none"
        ),
        step_ms=500,
        steps=(DINING_EAT_DURATION_MS // 500) + 50,
    )
    assert ate_done, "expected diner to finish eating and leave dining state"
    assert diner.satiety == MAX_WORKER_SATIETY
    assert diner.dining_canteen is None
    assert count_reserved_diner_slots(canteen) == 0
    assert diner.state == "idle"
