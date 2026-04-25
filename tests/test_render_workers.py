"""Worker render placement rules: assigned center, idle stack, orphan tile."""

from game.buildings.lumber_camp import LumberCamp
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.render import Renderer
from game.resources import ResourceManager
from game.world import World
from game.workers import Worker, WorkerManager, building_center_tile


def test_worker_grid_positions_assigned_worker_on_building_center() -> None:
    world = World()
    registry = BuildingRegistry(world)
    resources = ResourceManager()
    registry.place(TownHall, (16, 16))
    camp = registry.place(LumberCamp, (10, 10))
    wm = WorkerManager(resources, registry)
    w = Worker("LUMBERJACK")
    wm.add_worker(w)
    wm.assign_to_building(w, camp)
    pos = Renderer.worker_grid_positions(registry, wm)
    assert pos == [("LUMBERJACK", building_center_tile(camp))]


def test_worker_grid_positions_idle_workers_stack_next_to_town_hall() -> None:
    world = World()
    registry = BuildingRegistry(world)
    resources = ResourceManager()
    town_hall = registry.place(TownHall, (16, 16))
    wm = WorkerManager(resources, registry)
    wm.add_worker(Worker("LUMBERJACK", stand_tile=building_center_tile(town_hall)))
    wm.add_worker(Worker("FARMER", stand_tile=(0, 0)))
    thx, thy = building_center_tile(town_hall)
    pos = Renderer.worker_grid_positions(registry, wm)
    assert pos == [
        ("LUMBERJACK", (thx + 1, thy)),
        ("FARMER", (thx + 2, thy)),
    ]


def test_worker_grid_positions_orphan_stays_on_demolished_center() -> None:
    world = World()
    registry = BuildingRegistry(world)
    resources = ResourceManager()
    registry.place(TownHall, (16, 16))
    camp = registry.place(LumberCamp, (8, 8))
    wm = WorkerManager(resources, registry)
    w = Worker("LUMBERJACK")
    wm.add_worker(w)
    wm.assign_to_building(w, camp)
    center = building_center_tile(camp)
    registry.demolish(camp, wm)
    pos = Renderer.worker_grid_positions(registry, wm)
    assert pos == [("LUMBERJACK", center)]
