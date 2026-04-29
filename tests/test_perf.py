"""Optional perf sanity check for stress scene rendering."""

from __future__ import annotations

import time

import pygame

from game.buildings.lumber_camp import LumberCamp
from game.config import town_hall_origin_tile
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.render import Renderer
from game.world import World
from game.workers import Worker, WorkerManager


def test_render_stress_scene_avg_fps_at_least_55() -> None:
    surface = pygame.Surface((1280, 720))
    world = World()
    registry = BuildingRegistry(world)
    workers = WorkerManager(registry)
    registry.place(TownHall, town_hall_origin_tile())

    # Build up to 50 camps while respecting placement constraints.
    built = 0
    for y in range(2, 30, 3):
        for x in range(2, 30, 3):
            if built >= 50:
                break
            if registry.can_place(LumberCamp, (x, y)):
                registry.place(LumberCamp, (x, y))
                built += 1
        if built >= 50:
            break
    assert built == 50

    camps = [b for b in registry.all() if b.type_tag == "LUMBER_CAMP"]
    for camp in camps:
        w = Worker("LUMBERJACK")
        workers.add_worker(w)
        workers.assign_to_building(w, camp)
    assert len(workers.workers()) == 50

    frames = 60
    start = time.perf_counter()
    for _ in range(frames):
        surface.fill((20, 24, 22))
        Renderer.draw_world(surface, world)
        Renderer.draw_workers(surface, world, registry, workers)
    elapsed = time.perf_counter() - start
    avg_frame_ms = (elapsed / frames) * 1000.0
    assert avg_frame_ms <= (1000.0 / 55.0)
