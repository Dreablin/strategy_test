"""Dev placement tools: runtime tree/stone painting."""

import pygame

from game.buildings.registry import BuildingRegistry
from game.config import TILE_H, TILE_W
from game.iso import world_to_screen
from game.render import Renderer
from game.ui.placement import PlacementController
from game.world import World


def _cell_center_screen(surface: pygame.Surface, world: World, gx: int, gy: int) -> tuple[int, int]:
    ox, oy = Renderer.map_origin(surface, world)
    sx, sy = world_to_screen(gx, gy)
    return ox + sx + TILE_W // 2, oy + sy + TILE_H // 2


def test_dev_tree_tool_places_tree_on_free_tile() -> None:
    surface = pygame.Surface((1280, 720))
    world = World(world_seed=2)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    placement = PlacementController(world, registry)
    placement.select_dev("DEV_TREE")
    assert placement.try_place(surface, _cell_center_screen(surface, world, 12, 12))
    gx, gy = placement.hover_grid  # type: ignore[misc]
    assert world.tree_at(gx, gy) is not None


def test_dev_stone_tool_places_stone_on_free_tile() -> None:
    surface = pygame.Surface((1280, 720))
    world = World(world_seed=2)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    placement = PlacementController(world, registry)
    placement.select_dev("DEV_STONE")
    assert placement.try_place(surface, _cell_center_screen(surface, world, 13, 12))
    gx, gy = placement.hover_grid  # type: ignore[misc]
    assert world.stone_at(gx, gy) is not None


def test_dev_iron_tool_places_buildable_iron_on_free_tile() -> None:
    surface = pygame.Surface((1280, 720))
    world = World(world_seed=2)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    world._iron.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    placement = PlacementController(world, registry)
    placement.select_dev("DEV_IRON")
    assert placement.try_place(surface, _cell_center_screen(surface, world, 14, 12))
    gx, gy = placement.hover_grid  # type: ignore[misc]
    iron = world.iron_deposit_at(gx, gy)
    assert iron is not None
    assert iron.buildable


def test_dev_stone_tool_uses_random_variant(monkeypatch) -> None:
    surface = pygame.Surface((1280, 720))
    world = World(world_seed=2)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    placement = PlacementController(world, registry)
    placement.select_dev("DEV_STONE")
    monkeypatch.setattr("game.ui.placement.random.randint", lambda _a, _b: 3)
    assert placement.try_place(surface, _cell_center_screen(surface, world, 15, 12))
    gx, gy = placement.hover_grid  # type: ignore[misc]
    stone = world.stone_at(gx, gy)
    assert stone is not None
    assert stone.variant == 3


def test_dev_iron_tool_uses_random_variant(monkeypatch) -> None:
    surface = pygame.Surface((1280, 720))
    world = World(world_seed=2)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    world._iron.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    placement = PlacementController(world, registry)
    placement.select_dev("DEV_IRON")
    monkeypatch.setattr("game.ui.placement.random.randint", lambda _a, _b: 4)
    assert placement.try_place(surface, _cell_center_screen(surface, world, 16, 12))
    gx, gy = placement.hover_grid  # type: ignore[misc]
    iron = world.iron_deposit_at(gx, gy)
    assert iron is not None
    assert iron.variant == 4
