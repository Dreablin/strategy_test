"""Laboratory demolition cleanup for assigned Scientists (T405)."""

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


def _laboratory_with_scientists(
    *,
    level: int = 5,
    scientist_count: int = 3,
) -> tuple[BuildingRegistry, Laboratory, WorkerManager, list[Worker]]:
    world = World(world_seed=0)
    _clear_world(world)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    laboratory = registry.place(Laboratory, near_town_hall_tile(10, 10))
    laboratory.level = level
    laboratory.construction_site = None
    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    scientists: list[Worker] = []
    for _ in range(scientist_count):
        scientist = workers.hire("SCIENTIST")
        assert scientist is not None
        scientists.append(scientist)
    workers.reassign_all()
    assert workers.laboratory_assigned_scientist_count(laboratory) == scientist_count
    return registry, laboratory, workers, scientists


def test_demolish_laboratory_idles_all_assigned_scientists() -> None:
    registry, laboratory, workers, scientists = _laboratory_with_scientists(
        level=5,
        scientist_count=3,
    )
    registry.demolish(laboratory, workers)
    assert laboratory not in registry.all()
    for scientist in scientists:
        assert scientist.idle
        assert scientist.assigned_building is None
        assert scientist.state == "idle"
    assert workers.laboratory_assigned_scientist_count(laboratory) == 0


def test_notify_demolished_clears_multiple_scientists() -> None:
    registry, laboratory, workers, scientists = _laboratory_with_scientists(
        level=3,
        scientist_count=2,
    )
    workers.notify_demolished(laboratory)
    assert all(s.assigned_building is None and s.idle for s in scientists)


def test_demolish_laboratory_does_not_idle_scientists_at_other_buildings() -> None:
    world = World(world_seed=0)
    _clear_world(world)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    laboratory = registry.place(Laboratory, near_town_hall_tile(10, 10))
    laboratory.construction_site = None
    camp = registry.place(LumberCamp, near_town_hall_tile(14, 14))
    camp.construction_site = None
    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    at_lab = workers.hire("SCIENTIST")
    at_camp = Worker("LUMBERJACK", stand_tile=near_town_hall_tile(6, 6))
    assert at_lab is not None
    workers.add_worker(at_camp)
    workers.assign_to_building(at_lab, laboratory)
    workers.assign_to_building(at_camp, camp)

    registry.demolish(laboratory, workers)

    assert at_lab.assigned_building is None and at_lab.idle
    assert at_camp.assigned_building is camp and not at_camp.idle


def test_demolish_laboratory_parks_moving_scientist_at_current_tile() -> None:
    registry, laboratory, workers, scientists = _laboratory_with_scientists(
        level=1,
        scientist_count=1,
    )
    scientist = scientists[0]
    scientist.current_tile = (20, 20)
    scientist.state = "moving"
    scientist.idle = False
    scientist.path = [(21, 20)]

    registry.demolish(laboratory, workers)

    assert scientist.assigned_building is None
    assert scientist.idle
    assert scientist.stand_tile == (20, 20)
    assert scientist.path == []


def test_release_laboratory_scientists_direct_call() -> None:
    registry, laboratory, workers, scientists = _laboratory_with_scientists(
        level=4,
        scientist_count=2,
    )
    workers.release_laboratory_scientists(laboratory)
    assert all(s.assigned_building is None and s.idle for s in scientists)
    assert workers.laboratory_free_scientist_slots(laboratory) == laboratory.scientist_slot_capacity()


def test_reassign_after_demolish_does_not_attach_to_removed_laboratory() -> None:
    registry, laboratory, workers, scientists = _laboratory_with_scientists(
        level=1,
        scientist_count=1,
    )
    registry.demolish(laboratory, workers)
    scientist = scientists[0]
    assert scientist.assigned_building is None
    workers.reassign_all()
    assert scientist.assigned_building is None
    assert laboratory not in registry.all()
