"""Laboratory construction/upgrade pause for Scientists (T406)."""

from __future__ import annotations

from game.buildings.laboratory import Laboratory
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.construction import complete_construction
from game.worker_laboratory import building_has_free_staff_slot
from game.worker_status import production_status_for_building, worker_status_for_building
from game.workers import WorkerManager
from game.world import World


def _clear_world(world: World) -> None:
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    world._iron.clear()  # noqa: SLF001
    world.refresh_passability_tile_caches()


def _built_laboratory(*, level: int = 3) -> tuple[BuildingRegistry, Laboratory, WorkerManager]:
    world = World(world_seed=0)
    _clear_world(world)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    laboratory = registry.place(Laboratory, near_town_hall_tile(10, 10))
    laboratory.level = level
    laboratory.construction_site = None
    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    return registry, laboratory, workers


def _hire_and_staff(workers: WorkerManager, laboratory: Laboratory, count: int) -> list:
    scientists = []
    for _ in range(count):
        scientist = workers.hire("SCIENTIST")
        assert scientist is not None
        scientists.append(scientist)
    workers.reassign_all()
    assert workers.laboratory_active_scientist_count(laboratory) == count
    return scientists


def _finish_construction_site(laboratory: Laboratory) -> None:
    site = laboratory.construction_site
    assert site is not None
    for resource, amount in site.required_resources.items():
        site.delivered_resources[resource] = amount
    site.build_started_ms = 0
    now_ms = int(site.build_time_ms) + 1
    assert complete_construction(laboratory, now_ms=now_ms)


def test_upgrade_releases_all_assigned_scientists() -> None:
    registry, laboratory, workers = _built_laboratory(level=3)
    scientists = _hire_and_staff(workers, laboratory, 2)

    assert registry.upgrade_building(laboratory)

    assert laboratory.is_under_construction
    for scientist in scientists:
        assert scientist.assigned_building is None
        assert scientist.idle
    assert workers.laboratory_active_scientist_count(laboratory) == 0
    assert workers.laboratory_assigned_scientist_count(laboratory) == 0


def test_under_construction_shows_no_active_scientists_in_status() -> None:
    registry, laboratory, workers = _built_laboratory(level=1)
    _hire_and_staff(workers, laboratory, 1)
    assert registry.upgrade_building(laboratory)

    assert worker_status_for_building(workers, laboratory) == "empty"
    assert production_status_for_building(workers, laboratory) == "Under construction"


def test_scientists_not_reassigned_to_laboratory_under_construction() -> None:
    registry, laboratory, workers = _built_laboratory(level=1)
    scientists = _hire_and_staff(workers, laboratory, 1)
    assert registry.upgrade_building(laboratory)

    workers.reassign_all()
    assert all(s.assigned_building is None for s in scientists)
    assert not building_has_free_staff_slot(
        workers.workers(),
        laboratory,
        worker_type="SCIENTIST",
        is_staffed=workers.is_staffed(laboratory),
    )


def test_after_upgrade_completion_reassign_fills_slots() -> None:
    registry, laboratory, workers = _built_laboratory(level=1)
    scientists = _hire_and_staff(workers, laboratory, 1)
    assert registry.upgrade_building(laboratory)
    _finish_construction_site(laboratory)

    workers.reassign_all()
    assert workers.laboratory_active_scientist_count(laboratory) == 1
    assert scientists[0].assigned_building is laboratory


def test_assigned_scientist_reports_on_the_way_until_inside_laboratory() -> None:
    _, laboratory, workers = _built_laboratory(level=1)
    scientist = workers.hire("SCIENTIST")
    assert scientist is not None

    workers.reassign_all()
    assert scientist.assigned_building is laboratory
    assert workers.laboratory_active_scientist_count(laboratory) == 1
    assert workers.laboratory_research_contributing_scientist_count(laboratory) == 0
    assert worker_status_for_building(workers, laboratory) == "on the way"

    workers.assign_to_building(scientist, laboratory)
    assert workers.laboratory_research_contributing_scientist_count(laboratory) == 1
    assert worker_status_for_building(workers, laboratory) == "assigned"


def test_level_three_upgrade_refills_two_scientist_slots() -> None:
    registry, laboratory, workers = _built_laboratory(level=3)
    scientists = _hire_and_staff(workers, laboratory, 2)
    assert registry.upgrade_building(laboratory)
    _finish_construction_site(laboratory)

    workers.reassign_all()
    assert workers.laboratory_active_scientist_count(laboratory) == 2
    assert all(s.assigned_building is laboratory for s in scientists)


def test_pause_laboratory_scientists_direct_call() -> None:
    _, laboratory, workers = _built_laboratory(level=5)
    _hire_and_staff(workers, laboratory, 3)
    workers.pause_laboratory_scientists(laboratory)
    assert workers.laboratory_active_scientist_count(laboratory) == 0
    assert workers.laboratory_free_scientist_slots(laboratory) == laboratory.scientist_slot_capacity()


def test_placed_laboratory_under_initial_construction_has_no_active_scientists() -> None:
    world = World(world_seed=0)
    _clear_world(world)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    laboratory = registry.place(Laboratory, near_town_hall_tile(10, 10))
    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    scientist = workers.hire("SCIENTIST")
    assert scientist is not None

    workers.reassign_all()
    assert scientist.assigned_building is None
    assert workers.laboratory_active_scientist_count(laboratory) == 0
