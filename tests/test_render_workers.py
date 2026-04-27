"""Worker render placement rules: assigned center, idle tile, orphan tile, movement."""

import pygame

import game.assets as assets
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


def test_worker_grid_positions_idle_workers_stay_on_their_stand_tiles() -> None:
    world = World()
    registry = BuildingRegistry(world)
    resources = ResourceManager()
    town_hall = registry.place(TownHall, (16, 16))
    wm = WorkerManager(resources, registry)
    wm.add_worker(Worker("LUMBERJACK", stand_tile=building_center_tile(town_hall)))
    wm.add_worker(Worker("FARMER", stand_tile=(0, 0)))
    pos = Renderer.worker_grid_positions(registry, wm)
    assert pos == [
        ("LUMBERJACK", building_center_tile(town_hall)),
        ("FARMER", (0, 0)),
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


def test_draw_workers_moving_worker_pixel_shifts_between_frames(monkeypatch) -> None:
    world = World()
    registry = BuildingRegistry(world)
    resources = ResourceManager()
    registry.place(TownHall, (16, 16))
    wm = WorkerManager(resources, registry)
    w = Worker("LUMBERJACK", stand_tile=(5, 5))
    w.start_move([(5, 5), (6, 5)], started_ms=0)
    wm.add_worker(w)

    dot = pygame.Surface((1, 1), pygame.SRCALPHA)
    dot.fill((255, 0, 0, 255))
    monkeypatch.setattr(assets, "worker_dot", lambda _t: dot)

    surface = pygame.Surface((1280, 720), pygame.SRCALPHA)
    Renderer.draw_workers(surface, world, registry, wm)
    first = surface.get_bounding_rect()

    wm.update(1500)
    surface.fill((0, 0, 0, 0))
    Renderer.draw_workers(surface, world, registry, wm)
    second = surface.get_bounding_rect()

    assert first.width == 1 and first.height == 1
    assert second.width == 1 and second.height == 1
    assert second.x > first.x
