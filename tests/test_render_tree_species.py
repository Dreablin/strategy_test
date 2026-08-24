"""Failing render tests for tree species-aware sprite selection (T157)."""

from __future__ import annotations

import pygame

import game.assets as assets_mod
import game.render as render_mod
from game.render import Renderer
from game.trees import Tree, TreeStage
from game.world import World


def _dot(color: tuple[int, int, int]) -> pygame.Surface:
    surf = pygame.Surface((1, 1), pygame.SRCALPHA)
    surf.fill((*color, 255))
    return surf


def test_draw_trees_chooses_sprite_by_species_and_stage(monkeypatch) -> None:
    world = World(world_seed=0)
    world._trees.clear()  # noqa: SLF001
    center = (world.width // 2, world.height // 2)
    world._trees[center] = Tree(stage=TreeStage.ADULT, species=2)  # noqa: SLF001
    surface = pygame.Surface((1280, 720), pygame.SRCALPHA)

    calls: list[tuple[int, str]] = []
    monkeypatch.setattr(
        assets_mod,
        "tree_sprite",
        lambda stage, species=0: calls.append((species, stage)) or _dot((255, 0, 0)),
    )
    monkeypatch.setattr(
        render_mod,
        "tree_sprite",
        lambda stage, species=0: calls.append((species, stage)) or _dot((255, 0, 0)),
    )

    Renderer.draw_trees(surface, world)
    assert (2, "adult") in calls


def test_species_missing_asset_falls_back_without_crash(monkeypatch) -> None:
    world = World(world_seed=0)
    world._trees.clear()  # noqa: SLF001
    center = (world.width // 2, world.height // 2)
    world._trees[center] = Tree(stage=TreeStage.MATURE, species=1)  # noqa: SLF001
    surface = pygame.Surface((1280, 720), pygame.SRCALPHA)

    calls: list[tuple[int, str]] = []
    fallback = _dot((0, 255, 0))
    monkeypatch.setattr(
        assets_mod,
        "tree_sprite",
        lambda stage, species=0: calls.append((species, stage))
        or ((_ for _ in ()).throw(FileNotFoundError) if species == 1 else fallback),
    )
    monkeypatch.setattr(
        render_mod,
        "tree_sprite",
        lambda stage, species=0: calls.append((species, stage))
        or ((_ for _ in ()).throw(FileNotFoundError) if species == 1 else fallback),
    )

    # Should not raise; renderer should fallback to a drawable sprite path.
    Renderer.draw_trees(surface, world)
    assert (1, "mature") in calls


def test_tree_species_does_not_change_tree_layering_order() -> None:
    world = World(world_seed=0)
    world._trees.clear()  # noqa: SLF001
    # Same draw-order relation regardless of species labels.
    world._trees[(20, 20)] = Tree(stage=TreeStage.ADULT, species=2)  # noqa: SLF001
    world._trees[(21, 20)] = Tree(stage=TreeStage.ADULT, species=0)  # noqa: SLF001
    entries = sorted(world.iter_alive_trees(), key=lambda item: (item[0][0] + item[0][1], item[0][0]))
    assert [pos for pos, _tree in entries] == [(20, 20), (21, 20)]
