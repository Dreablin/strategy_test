"""Phase 21 smoke: farm + fields loop through sow/grow/harvest/export repeatedly."""

from __future__ import annotations

from game.buildings.farm import Farm
from game.buildings.field import WHEAT_EMPTY, WHEAT_PHASE_1, WHEAT_PHASE_2, WHEAT_PHASE_4, Field
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.world import World
from game.workers import WorkerManager


def _tick(workers: WorkerManager, now_ms: dict[str, int], dt_ms: int = 500) -> None:
    now_ms["t"] += dt_ms
    workers.reassign_all()
    workers.update(now_ms["t"])


def _advance_until(
    workers: WorkerManager,
    now_ms: dict[str, int],
    predicate,
    *,
    steps: int = 3000,
    dt_ms: int = 500,
) -> bool:
    for _ in range(steps):
        _tick(workers, now_ms, dt_ms)
        if predicate():
            return True
    return False


def test_smoke_phase21_farm_field_wheat_export_loop_repeats() -> None:
    now_ms = {"t": 0}
    world = World(world_seed=21)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    farm = registry.place(Farm, near_town_hall_tile(20, 12))
    farm.construction_site = None
    fx, fy = farm.grid_pos
    candidate_tiles = [
        (fx + dx, fy + dy)
        for dx in range(-5, 6)
        for dy in range(-5, 6)
        if not (dx == 0 and dy == 0)
    ]
    fields: list[Field] = []
    for tile in candidate_tiles:
        if not registry.can_place(Field, tile):
            continue
        fields.append(registry.place(Field, tile))
        if len(fields) == 3:
            break
    assert len(fields) == 3, "expected three valid field positions near the farm"
    assert all(field.is_under_construction for field in fields)

    workers = WorkerManager(registry, now_ms_fn=lambda: now_ms["t"])
    for field in fields:
        workers._write_field_phase(field, WHEAT_EMPTY)  # noqa: SLF001
    assert workers.hire("BUILDER") is not None
    farmer = workers.hire("FARMER")
    assert farmer is not None

    built_fields = _advance_until(workers, now_ms, lambda: all(not f.is_under_construction for f in fields))
    assert built_fields, "expected builder to complete all field construction sites"
    assigned_farmer = _advance_until(workers, now_ms, lambda: farmer.assigned_building is farm, steps=800)
    assert assigned_farmer, "expected farmer to be assigned to farm"

    focus_field = fields[0]
    for field in fields[1:]:
        workers._write_field_phase(field, WHEAT_PHASE_2)  # noqa: SLF001
    workers._write_field_phase(focus_field, WHEAT_EMPTY)  # noqa: SLF001
    sowed_phase1 = _advance_until(
        workers,
        now_ms,
        lambda: workers._read_field_phase(focus_field) == WHEAT_PHASE_1,  # noqa: SLF001
        steps=1200,
    )
    assert sowed_phase1, "expected farmer to sow field from EMPTY to PHASE_1"
    workers._write_field_phase(focus_field, WHEAT_PHASE_4)  # noqa: SLF001

    harvested_reset = _advance_until(
        workers,
        now_ms,
        lambda: workers._read_field_phase(focus_field) == WHEAT_EMPTY,  # noqa: SLF001
        steps=2000,
    )
    assert harvested_reset, "expected farmer to harvest ripe wheat and reset the field to EMPTY"
    deposited_to_farm = _advance_until(workers, now_ms, lambda: farm.stored >= 1, steps=2000)
    assert deposited_to_farm, "expected harvested wheat deposited to farm local storage"
    assert workers.hire("CARRIER") is not None
    exported_once = _advance_until(workers, now_ms, lambda: town_hall.warehouse_amount("wheat") >= 1, steps=2000)
    assert exported_once, "expected carrier to export farm wheat via shared transport queue"

    repeated_sow = _advance_until(
        workers,
        now_ms,
        lambda: workers._read_field_phase(focus_field) == WHEAT_PHASE_1,  # noqa: SLF001
        steps=2000,
    )
    assert repeated_sow, "expected farmer cycle to repeat and resow harvested field"
    workers._write_field_phase(focus_field, WHEAT_PHASE_4)  # noqa: SLF001

    repeated_harvest = _advance_until(
        workers,
        now_ms,
        lambda: workers._read_field_phase(focus_field) == WHEAT_EMPTY,  # noqa: SLF001
        steps=2000,
    )
    assert repeated_harvest, "expected second harvest cycle on the same field"
    exported_twice = _advance_until(workers, now_ms, lambda: town_hall.warehouse_amount("wheat") >= 2, steps=2500)
    assert exported_twice, "expected production/export loop to repeat beyond the first wheat delivery"
