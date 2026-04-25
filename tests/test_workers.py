"""Worker manager: demolition orphans workers on the former building center (PRD F-DEMO-02)."""

from game.buildings.lumber_camp import LumberCamp
from game.buildings.registry import BuildingRegistry
from game.world import World
from game.workers import Worker, WorkerManager, building_center_tile


def test_building_center_tile_for_2x2() -> None:
    b = LumberCamp(level=1, grid_pos=(10, 8))
    assert building_center_tile(b) == (11, 9)


def test_demolition_parks_assigned_worker_on_center_tile() -> None:
    world = World()
    registry = BuildingRegistry(world)
    camp = registry.place(LumberCamp, (14, 14))
    wm = WorkerManager()
    w = Worker("LUMBERJACK")
    wm.add_worker(w)
    wm.assign_to_building(w, camp)
    assert not w.idle
    registry.demolish(camp, wm)
    assert w.idle
    assert w.assigned_building is None
    assert w.stand_tile == (15, 15)


def test_demolition_does_not_affect_other_workers() -> None:
    world = World()
    registry = BuildingRegistry(world)
    a = registry.place(LumberCamp, (5, 5))
    b = registry.place(LumberCamp, (20, 20))
    wm = WorkerManager()
    w1 = Worker("LUMBERJACK")
    w2 = Worker("LUMBERJACK")
    wm.add_worker(w1)
    wm.add_worker(w2)
    wm.assign_to_building(w1, a)
    wm.assign_to_building(w2, b)
    registry.demolish(a, wm)
    assert w1.idle and w1.assigned_building is None
    assert not w2.idle and w2.assigned_building is b
