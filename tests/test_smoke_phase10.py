"""Phase 10 smoke integration: tree block, clear-on-place, occlusion."""

from __future__ import annotations

import pygame

import game.assets as assets_mod
import game.render as render_mod
from game.buildings.lumber_camp import LumberCamp
from game.config import town_hall_origin_tile, near_town_hall_tile
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.iso import world_to_screen
from game.pathfinding import find_path_bfs
from game.render import Renderer
from game.trees import Tree, TreeStage
from game.world import World
from game.workers import Worker, WorkerManager


def _tree_pixel(surface: pygame.Surface, world: World, gx: int, gy: int) -> tuple[int, int]:
    ox, oy = Renderer.map_origin(surface, world)
    sx, sy = world_to_screen(gx, gy)
    return (ox + sx + 32, oy + sy + 31)


def test_smoke_phase10_tree_features(monkeypatch) -> None:
    # 1) Movement blocking by tree.
    world = World(world_seed=2)
    world._trees[(12, 10)] = Tree(stage=TreeStage.ADULT)  # noqa: SLF001
    path = find_path_bfs(world, (10, 10), (14, 10), blocked=set())
    assert path is not None
    assert (12, 10) not in path

    # 2) Placement clears tree inside footprint.
    registry = BuildingRegistry(world)
    th = registry.place(TownHall, town_hall_origin_tile())
    th.level = 5
    tx, ty = near_town_hall_tile()
    world._trees[(tx, ty)] = Tree(stage=TreeStage.ADULT)  # noqa: SLF001
    assert world.is_tree_blocking(tx, ty)
    camp = registry.place(LumberCamp, (tx, ty))
    assert camp is not None
    assert not world.is_tree_blocking(tx, ty)

    # 3) Tree occludes worker behind on same tile.
    workers = WorkerManager(registry)
    workers.add_worker(Worker("LUMBERJACK", stand_tile=(tx, ty)))
    world._trees[(tx, ty)] = Tree(stage=TreeStage.ADULT)  # noqa: SLF001

    dot = pygame.Surface((1, 1), pygame.SRCALPHA)
    dot.fill((255, 0, 0, 255))
    monkeypatch.setattr(assets_mod, "worker_dot", lambda _t: dot)
    tree = pygame.Surface((1, 1), pygame.SRCALPHA)
    tree.fill((0, 255, 0, 255))
    monkeypatch.setattr(render_mod, "tree_sprite", lambda _s: tree)

    surface = pygame.Surface((1280, 720), pygame.SRCALPHA)
    surface.fill((20, 24, 22))
    Renderer.draw_world(surface, world)
    Renderer.draw_buildings(surface, world, registry)
    Renderer.draw_workers(surface, world, registry, workers)
    Renderer.draw_trees(surface, world)
    px = _tree_pixel(surface, world, tx, ty)
    assert surface.get_at(px)[:3] == (0, 255, 0)
