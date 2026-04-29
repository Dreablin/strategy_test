"""Failing tree layering tests for Phase 10 (T73)."""

import pygame

import game.assets as assets_mod
import game.render as render_mod
from game.buildings.registry import BuildingRegistry
from game.config import town_hall_origin_tile, near_town_hall_tile
from game.buildings.town_hall import TownHall
from game.iso import world_to_screen
from game.render import Renderer
from game.trees import Tree, TreeStage
from game.world import World
from game.workers import Worker, WorkerManager

_BG = (20, 24, 22)


def _draw_scene(
    surface: pygame.Surface,
    world: World,
    registry: BuildingRegistry,
    workers: WorkerManager,
) -> None:
    surface.fill(_BG)
    Renderer.draw_world(surface, world)
    Renderer.draw_buildings(surface, world, registry)
    Renderer.draw_workers(surface, world, registry, workers)
    Renderer.draw_trees(surface, world)


def _tree_pixel(surface: pygame.Surface, world: World, gx: int, gy: int) -> tuple[int, int]:
    ox, oy = Renderer.map_origin(surface, world)
    sx, sy = world_to_screen(gx, gy)
    return (ox + sx + 32, oy + sy + 31)


def _worker_pixel(surface: pygame.Surface, world: World, gx: int, gy: int) -> tuple[int, int]:
    ox, oy = Renderer.map_origin(surface, world)
    sx, sy = world_to_screen(gx, gy)
    return (ox + sx + 32, oy + sy + 16)


def test_draw_trees_callable_exists() -> None:
    assert callable(getattr(Renderer, "draw_trees", None))


def test_tree_occludes_worker_behind(monkeypatch) -> None:
    world = World()
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    workers = WorkerManager(registry)
    tx, ty = near_town_hall_tile()
    w = Worker("LUMBERJACK", stand_tile=(tx, ty))
    workers.add_worker(w)
    world._trees[(tx, ty)] = Tree(stage=TreeStage.ADULT)  # noqa: SLF001

    dot = pygame.Surface((1, 1), pygame.SRCALPHA)
    dot.fill((255, 0, 0, 255))
    monkeypatch.setattr(assets_mod, "worker_dot", lambda _t: dot)
    tree = pygame.Surface((1, 1), pygame.SRCALPHA)
    tree.fill((0, 255, 0, 255))
    monkeypatch.setattr(render_mod, "tree_sprite", lambda _s: tree)

    surface = pygame.Surface((1280, 720), pygame.SRCALPHA)
    _draw_scene(surface, world, registry, workers)
    px = _tree_pixel(surface, world, tx, ty)
    assert surface.get_at(px)[:3] == (0, 255, 0)


def test_worker_in_front_remains_visible(monkeypatch) -> None:
    world = World()
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    workers = WorkerManager(registry)
    tx, ty = near_town_hall_tile()
    w = Worker("LUMBERJACK", stand_tile=(tx + 1, ty + 1))
    workers.add_worker(w)
    world._trees[(tx, ty)] = Tree(stage=TreeStage.ADULT)  # noqa: SLF001

    dot = pygame.Surface((1, 1), pygame.SRCALPHA)
    dot.fill((255, 0, 0, 255))
    monkeypatch.setattr(assets_mod, "worker_dot", lambda _t: dot)
    tree = pygame.Surface((1, 1), pygame.SRCALPHA)
    tree.fill((0, 255, 0, 255))
    monkeypatch.setattr(render_mod, "tree_sprite", lambda _s: tree)

    surface = pygame.Surface((1280, 720), pygame.SRCALPHA)
    _draw_scene(surface, world, registry, workers)
    px_tree = _tree_pixel(surface, world, tx, ty)
    px_worker = _worker_pixel(surface, world, tx + 1, ty + 1)
    assert surface.get_at(px_tree)[:3] == (0, 255, 0)
    assert surface.get_at(px_worker)[:3] == (255, 0, 0)
