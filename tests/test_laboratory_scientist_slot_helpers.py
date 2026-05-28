"""Laboratory multi-slot counting helper tests (T403)."""

from __future__ import annotations

from game.buildings.laboratory import Laboratory
from game.buildings.registry import BuildingRegistry
from game.buildings.school import School
from game.buildings.town_hall import TownHall
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.workers import WorkerManager
from game.world import World


def _laboratory_fixture(*, level: int = 3) -> tuple[BuildingRegistry, Laboratory, WorkerManager]:
    world = World(world_seed=0)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    world._iron.clear()  # noqa: SLF001
    world.refresh_passability_tile_caches()
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    laboratory = registry.place(Laboratory, near_town_hall_tile(10, 10))
    laboratory.level = level
    laboratory.construction_site = None
    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    return registry, laboratory, workers


def test_empty_laboratory_reports_full_free_slots() -> None:
    _, laboratory, workers = _laboratory_fixture(level=3)
    assert laboratory.scientist_slot_capacity() == 2
    assert workers.laboratory_assigned_scientist_count(laboratory) == 0
    assert workers.laboratory_free_scientist_slots(laboratory) == 2
    assert workers.laboratory_assigned_scientists(laboratory) == ()


def test_manual_assignments_reduce_free_slots() -> None:
    _, laboratory, workers = _laboratory_fixture(level=3)
    first = workers.hire("SCIENTIST")
    second = workers.hire("SCIENTIST")
    assert first is not None and second is not None
    workers.assign_to_building(first, laboratory)
    assert workers.laboratory_assigned_scientist_count(laboratory) == 1
    assert workers.laboratory_free_scientist_slots(laboratory) == 1
    assert tuple(workers.laboratory_assigned_scientists(laboratory)) == (first,)

    workers.assign_to_building(second, laboratory)
    assert workers.laboratory_assigned_scientist_count(laboratory) == 2
    assert workers.laboratory_free_scientist_slots(laboratory) == 0
    assert set(workers.laboratory_assigned_scientists(laboratory)) == {first, second}


def test_over_capacity_assignment_still_counts_all_scientists() -> None:
    _, laboratory, workers = _laboratory_fixture(level=1)
    assert laboratory.scientist_slot_capacity() == 1
    scientists = [workers.hire("SCIENTIST") for _ in range(2)]
    assert all(s is not None for s in scientists)
    for scientist in scientists:
        assert scientist is not None
        workers.assign_to_building(scientist, laboratory)
    assert workers.laboratory_assigned_scientist_count(laboratory) == 2
    assert workers.laboratory_free_scientist_slots(laboratory) == 0


def test_non_laboratory_building_reports_zero() -> None:
    registry = BuildingRegistry(World(world_seed=0))
    registry.place(TownHall, town_hall_origin_tile())
    school = registry.place(School, near_town_hall_tile(8, 8))
    workers = WorkerManager(registry)
    assert workers.laboratory_assigned_scientist_count(school) == 0
    assert workers.laboratory_free_scientist_slots(school) == 0
    assert workers.laboratory_assigned_scientists(school) == ()


def test_other_workers_assigned_to_laboratory_are_not_counted() -> None:
    _, laboratory, workers = _laboratory_fixture(level=5)
    carrier = workers.hire("CARRIER")
    assert carrier is not None
    workers.assign_to_building(carrier, laboratory)
    assert workers.laboratory_assigned_scientist_count(laboratory) == 0
    assert workers.laboratory_free_scientist_slots(laboratory) == laboratory.scientist_slot_capacity()


def test_level_ten_capacity_five_slots() -> None:
    _, laboratory, workers = _laboratory_fixture(level=10)
    assert laboratory.scientist_slot_capacity() == 5
    assert workers.laboratory_free_scientist_slots(laboratory) == 5
