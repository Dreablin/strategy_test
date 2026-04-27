"""Failing tree layering tests for Phase 10 (T73)."""

import pygame

import game.assets as assets_mod
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.render import Renderer
from game.resources import ResourceManager
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


def test_draw_trees_callable_exists() -> None:
    assert callable(getattr(Renderer, "draw_trees", None))


def test_tree_occludes_worker_behind(monkeypatch) -> None:
    world = World()
    registry = BuildingRegistry(world)
    resources = ResourceManager()
    registry.place(TownHall, (16, 16))
    workers = WorkerManager(resources, registry)
    w = Worker("LUMBERJACK", stand_tile=(10, 10))
    workers.add_worker(w)
    world._trees[(10, 10)] = world._trees.get((10, 10)) or world.tree_at(0, 0)  # noqa: SLF001

    dot = pygame.Surface((1, 1), pygame.SRCALPHA)
    dot.fill((255, 0, 0, 255))
    monkeypatch.setattr(assets_mod, "worker_dot", lambda _t: dot)
    tree = pygame.Surface((1, 1), pygame.SRCALPHA)
    tree.fill((0, 255, 0, 255))
    monkeypatch.setattr(assets_mod, "tree_sprite", lambda _s: tree)

    surface = pygame.Surface((1280, 720), pygame.SRCALPHA)
    _draw_scene(surface, world, registry, workers)
    rect = surface.get_bounding_rect()
    assert surface.get_at((rect.x, rect.y))[:3] == (0, 255, 0)


def test_worker_in_front_remains_visible(monkeypatch) -> None:
    world = World()
    registry = BuildingRegistry(world)
    resources = ResourceManager()
    registry.place(TownHall, (16, 16))
    workers = WorkerManager(resources, registry)
    w = Worker("LUMBERJACK", stand_tile=(11, 11))
    workers.add_worker(w)
    world._trees[(10, 10)] = world._trees.get((10, 10)) or world.tree_at(0, 0)  # noqa: SLF001

    dot = pygame.Surface((1, 1), pygame.SRCALPHA)
    dot.fill((255, 0, 0, 255))
    monkeypatch.setattr(assets_mod, "worker_dot", lambda _t: dot)
    tree = pygame.Surface((1, 1), pygame.SRCALPHA)
    tree.fill((0, 255, 0, 255))
    monkeypatch.setattr(assets_mod, "tree_sprite", lambda _s: tree)

    surface = pygame.Surface((1280, 720), pygame.SRCALPHA)
    _draw_scene(surface, world, registry, workers)
    rect = surface.get_bounding_rect()
    # With worker in front, the top-most pixel in the composite should be worker red.
    assert surface.get_at((rect.x, rect.y))[:3] == (255, 0, 0)
