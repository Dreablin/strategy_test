"""Runtime tests for farmer sow action loop (T233)."""

from __future__ import annotations

from game.buildings.farm import Farm
from game.buildings.field import WHEAT_EMPTY, WHEAT_PHASE_1, WHEAT_PHASE_4
from game.buildings.field import Field
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.world import World
from game.workers import WorkerManager


def _advance(workers: WorkerManager, now_ms: dict[str, int], *, steps: int = 2000, step_ms: int = 500) -> None:
    for _ in range(steps):
        now_ms["t"] += step_ms
        workers.reassign_all()
        workers.update(now_ms["t"])


def _advance_until_phase(
    workers: WorkerManager,
    now_ms: dict[str, int],
    field: Field,
    phase: str,
    *,
    max_steps: int = 300,
    step_ms: int = 500,
) -> None:
    for _ in range(max_steps):
        now_ms["t"] += step_ms
        workers.reassign_all()
        workers.update(now_ms["t"])
        if workers._read_field_phase(field) == phase:  # noqa: SLF001
            return
    raise AssertionError(f"field never reached {phase}")


def test_farmer_sows_empty_field_to_phase_1_after_action_time() -> None:
    now_ms = {"t": 0}
    world = World(world_seed=1)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    farm = registry.place(Farm, near_town_hall_tile(10, 8))
    farm.construction_site = None
    field = registry.place(Field, near_town_hall_tile(7, 8))
    field.construction_site = None

    workers = WorkerManager(registry, now_ms_fn=lambda: now_ms["t"])
    workers._write_field_phase(field, WHEAT_EMPTY)  # noqa: SLF001
    farmer = workers.hire("FARMER")
    assert farmer is not None

    _advance_until_phase(workers, now_ms, field, WHEAT_PHASE_1)

    assert workers._read_field_phase(field) == WHEAT_PHASE_1  # noqa: SLF001
    assert farmer.state in {"returning", "resting", "working_field"}


def test_farmer_treats_newly_built_field_as_empty_and_can_sow() -> None:
    now_ms = {"t": 0}
    world = World(world_seed=11)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    farm = registry.place(Farm, near_town_hall_tile(10, 8))
    farm.construction_site = None
    field = registry.place(Field, near_town_hall_tile(7, 8))
    field.construction_site = None
    workers = WorkerManager(registry, now_ms_fn=lambda: now_ms["t"])
    farmer = workers.hire("FARMER")
    assert farmer is not None

    # No explicit _write_field_phase call: freshly built field should be considered EMPTY.
    _advance(workers, now_ms, steps=220, step_ms=500)
    assert workers._read_field_phase(field) == WHEAT_PHASE_1  # noqa: SLF001


def test_farmer_waits_full_rest_interval_before_next_dispatch_after_sow() -> None:
    now_ms = {"t": 0}
    world = World(world_seed=2)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    farm = registry.place(Farm, near_town_hall_tile(10, 8))
    farm.construction_site = None
    field = registry.place(Field, near_town_hall_tile(7, 8))
    field.construction_site = None
    workers = WorkerManager(registry, now_ms_fn=lambda: now_ms["t"])
    workers._write_field_phase(field, WHEAT_EMPTY)  # noqa: SLF001
    farmer = workers.hire("FARMER")
    assert farmer is not None

    _advance(workers, now_ms, steps=200, step_ms=500)
    assert farmer.state == "resting"
    rest_until = farmer.camp_wait_until_ms
    assert rest_until > now_ms["t"]

    while now_ms["t"] + 500 < rest_until:
        now_ms["t"] += 500
        workers.reassign_all()
        workers.update(now_ms["t"])
        assert farmer.state == "resting"


def test_farmer_waits_full_rest_interval_before_next_dispatch_after_harvest() -> None:
    now_ms = {"t": 0}
    world = World(world_seed=3)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    farm = registry.place(Farm, near_town_hall_tile(10, 8))
    farm.construction_site = None
    field = registry.place(Field, near_town_hall_tile(7, 8))
    field.construction_site = None
    workers = WorkerManager(registry, now_ms_fn=lambda: now_ms["t"])
    workers._write_field_phase(field, WHEAT_PHASE_4)  # noqa: SLF001
    farmer = workers.hire("FARMER")
    assert farmer is not None

    _advance(workers, now_ms, steps=250, step_ms=500)
    assert farmer.state == "resting"
    rest_until = farmer.camp_wait_until_ms
    assert rest_until > now_ms["t"]

    while now_ms["t"] + 500 < rest_until:
        now_ms["t"] += 500
        workers.reassign_all()
        workers.update(now_ms["t"])
        assert farmer.state == "resting"


def test_farmer_does_not_start_new_harvest_when_farm_storage_is_full() -> None:
    now_ms = {"t": 0}
    world = World(world_seed=4)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    farm = registry.place(Farm, near_town_hall_tile(10, 8))
    farm.construction_site = None
    field = registry.place(Field, near_town_hall_tile(7, 8))
    field.construction_site = None
    workers = WorkerManager(registry, now_ms_fn=lambda: now_ms["t"])
    workers._write_field_phase(field, WHEAT_PHASE_4)  # noqa: SLF001
    farm.stored = farm.storage_capacity()
    farmer = workers.hire("FARMER")
    assert farmer is not None

    _advance(workers, now_ms, steps=220, step_ms=500)

    assert workers._read_field_phase(field) == WHEAT_PHASE_4  # noqa: SLF001
    assert farmer.state in {"resting", "working_field"}


def test_two_farmers_do_not_target_same_field() -> None:
    now_ms = {"t": 0}
    world = World(world_seed=5)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    farm_a = registry.place(Farm, (20, 20))
    farm_b = registry.place(Farm, (25, 20))
    farm_a.construction_site = None
    farm_b.construction_site = None
    field = registry.place(Field, (23, 23))
    field.construction_site = None
    workers = WorkerManager(registry, now_ms_fn=lambda: now_ms["t"])
    workers._write_field_phase(field, WHEAT_EMPTY)  # noqa: SLF001
    farmer_a = workers.hire("FARMER")
    farmer_b = workers.hire("FARMER")
    assert farmer_a is not None
    assert farmer_b is not None

    for _ in range(500):
        now_ms["t"] += 500
        workers.reassign_all()
        workers.update(now_ms["t"])
        if any(
            farmer.target_tree == field.grid_pos and farmer.state in {"going_to_field", "sowing"}
            for farmer in (farmer_a, farmer_b)
        ):
            break

    targeted = [
        farmer
        for farmer in (farmer_a, farmer_b)
        if farmer.target_tree == field.grid_pos and farmer.state in {"going_to_field", "sowing"}
    ]
    assert len(targeted) == 1
    assert all(
        farmer.target_tree != field.grid_pos
        for farmer in (farmer_a, farmer_b)
        if farmer not in targeted
    )

