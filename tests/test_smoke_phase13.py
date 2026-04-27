"""Phase 13 end-of-phase smoke: orthogonal paths, bounded path calls, render sanity."""

from __future__ import annotations

import game.workers as workers_mod
from game.buildings.lumber_camp import LumberCamp
from game.buildings.registry import BuildingRegistry
from game.buildings.stone_mine import StoneMine
from game.buildings.town_hall import TownHall
from game.render import Renderer
from game.resources import ResourceManager
from game.stones import Stone
from game.trees import Tree, TreeStage
from game.world import World
from game.workers import WorkerManager

import pygame


def test_smoke_phase13_paths_calls_and_render() -> None:
    world = World()
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    world._trees[(24, 20)] = Tree(stage=TreeStage.ADULT)  # noqa: SLF001
    world._trees[(25, 20)] = Tree(stage=TreeStage.ADULT)  # noqa: SLF001
    world._trees[(26, 20)] = Tree(stage=TreeStage.ADULT)  # noqa: SLF001
    world._stones[(30, 20)] = Stone(units=10)  # noqa: SLF001
    world._stones[(31, 20)] = Stone(units=10)  # noqa: SLF001

    resources = ResourceManager()
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, (16, 16))
    town_hall.level = 3
    camp = registry.place(LumberCamp, (22, 22))
    mine = registry.place(StoneMine, (28, 22))

    now_ms = {"t": 0}
    manager = WorkerManager(resources, registry, now_ms_fn=lambda: now_ms["t"])
    assert manager.hire("LUMBERJACK") is not None
    assert manager.hire("STONECUTTER") is not None

    calls = {"n": 0}
    steps: list[tuple[tuple[int, int], tuple[int, int]]] = []
    real = workers_mod.find_path_bfs

    def counted(*args, **kwargs):  # noqa: ANN002, ANN003
        calls["n"] += 1
        path = real(*args, **kwargs)
        if path is not None:
            steps.extend((a, b) for a, b in zip(path, path[1:]))
        return path

    workers_mod.find_path_bfs = counted
    try:
        for _ in range(60_000 // 16):
            now_ms["t"] += 16
            manager.reassign_all()
            manager.update(now_ms["t"])
    finally:
        workers_mod.find_path_bfs = real

    assert camp is not None and mine is not None
    assert steps, "expected at least one path step recorded"
    assert all(abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1 for a, b in steps)
    assert calls["n"] < 200

    bg = (20, 24, 22, 255)
    surface = pygame.Surface((320, 240), pygame.SRCALPHA)
    surface.fill(bg)
    Renderer.draw_world(surface, world)
    Renderer.draw_buildings(surface, world, registry)
    Renderer.draw_workers(surface, world, registry, manager)
    Renderer.draw_trees(surface, world)
    Renderer.draw_stones(surface, world)

    has_non_bg = any(surface.get_at((x, y)) != bg for y in range(240) for x in range(320))
    assert has_non_bg
