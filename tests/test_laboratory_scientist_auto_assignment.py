"""Automatic multi-Scientist Laboratory assignment tests (T404)."""

from __future__ import annotations

from game.buildings.laboratory import Laboratory
from game.buildings.lumber_camp import LumberCamp
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.workers import Worker, WorkerManager
from game.world import World


def _clear_world(world: World) -> None:
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    world._iron.clear()  # noqa: SLF001
    world.refresh_passability_tile_caches()


def _laboratory_setup(*, level: int) -> tuple[WorkerManager, Laboratory]:
    world = World(world_seed=0)
    _clear_world(world)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    laboratory = registry.place(Laboratory, near_town_hall_tile(10, 10))
    laboratory.level = level
    laboratory.construction_site = None
    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    return workers, laboratory


def _hire_scientists(workers: WorkerManager, count: int) -> list[Worker]:
    hired: list[Worker] = []
    for _ in range(count):
        scientist = workers.hire("SCIENTIST")
        assert scientist is not None
        hired.append(scientist)
    return hired


def test_level_one_laboratory_assigns_only_one_scientist() -> None:
    workers, laboratory = _laboratory_setup(level=1)
    scientists = _hire_scientists(workers, 2)
    workers.reassign_all()
    assigned = [s for s in scientists if s.assigned_building is laboratory]
    idle = [s for s in scientists if s.assigned_building is None and s.idle]
    assert len(assigned) == 1
    assert len(idle) == 1


def test_level_three_laboratory_assigns_two_scientists() -> None:
    workers, laboratory = _laboratory_setup(level=3)
    scientists = _hire_scientists(workers, 2)
    workers.reassign_all()
    assert all(s.assigned_building is laboratory for s in scientists)
    assert workers.laboratory_assigned_scientist_count(laboratory) == 2
    assert workers.laboratory_free_scientist_slots(laboratory) == 0


def test_level_six_laboratory_assigns_three_scientists() -> None:
    workers, laboratory = _laboratory_setup(level=6)
    scientists = _hire_scientists(workers, 3)
    workers.reassign_all()
    assert len([s for s in scientists if s.assigned_building is laboratory]) == 3


def test_level_ten_laboratory_assigns_up_to_five_scientists() -> None:
    workers, laboratory = _laboratory_setup(level=10)
    scientists = _hire_scientists(workers, 6)
    workers.reassign_all()
    assigned = [s for s in scientists if s.assigned_building is laboratory]
    idle = [s for s in scientists if s.assigned_building is None and s.idle]
    assert len(assigned) == 5
    assert len(idle) == 1
    assert workers.laboratory_free_scientist_slots(laboratory) == 0


def test_lumber_camp_still_one_worker_per_building() -> None:
    world = World(world_seed=0)
    _clear_world(world)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    camp = registry.place(LumberCamp, near_town_hall_tile(8, 8))
    camp.construction_site = None
    cx, cy = camp.grid_pos  # type: ignore[assignment]
    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    w1 = Worker("LUMBERJACK", stand_tile=(cx - 4, cy))
    w2 = Worker("LUMBERJACK", stand_tile=(cx - 3, cy))
    workers.add_worker(w1)
    workers.add_worker(w2)
    workers.reassign_all()
    assigned = [w for w in (w1, w2) if w.assigned_building is camp]
    assert len(assigned) == 1
