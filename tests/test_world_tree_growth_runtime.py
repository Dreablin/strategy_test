"""Failing world runtime tests for planted trees and timed growth (T151)."""

from __future__ import annotations

from game.config import town_hall_footprint_tiles
from game.stones import Stone
from game.trees import Tree
from game.trees import TreeStage
from game.world import World, find_nearest_free_tree


def _clear_resource_layers(world: World) -> None:
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001


def test_world_generated_trees_are_adult_without_growth_timer() -> None:
    world = World(world_seed=42)
    trees = list(world.iter_alive_trees())
    assert trees
    for _pos, tree in trees:
        assert tree.stage == TreeStage.ADULT
        assert tree.next_growth_at_ms is None


def test_plant_tree_creates_sapling_on_valid_free_tile() -> None:
    world = World(world_seed=0)
    _clear_resource_layers(world)

    planted = world.plant_tree(5, 5, now_ms=1_000, species=2)
    assert planted is not None
    assert planted.stage == TreeStage.SAPLING
    assert planted.species == 2
    assert planted.next_growth_at_ms == 31_000
    assert world.tree_at(5, 5) is planted


def test_plant_tree_without_species_uses_random_species(monkeypatch) -> None:
    world = World(world_seed=0)
    _clear_resource_layers(world)
    monkeypatch.setattr("game.world.random.randint", lambda _a, _b: 1)
    planted = world.plant_tree(6, 6, now_ms=0)
    assert planted is not None
    assert planted.species == 1


def test_plant_tree_rejects_occupied_stone_existing_and_th_tiles() -> None:
    world = World(world_seed=0)
    _clear_resource_layers(world)

    world.mark_occupied(2, 2, 1, 1)
    assert world.plant_tree(2, 2, now_ms=0, species=0) is None

    world._stones[(3, 3)] = Stone()  # noqa: SLF001
    assert world.plant_tree(3, 3, now_ms=0, species=1) is None

    world._trees[(4, 4)] = Tree(stage=TreeStage.ADULT, species=1)  # noqa: SLF001
    assert world.plant_tree(4, 4, now_ms=0, species=2) is None

    tx, ty = next(iter(town_hall_footprint_tiles()))
    assert world.plant_tree(tx, ty, now_ms=0, species=0) is None


def test_update_tree_growth_advances_planted_trees_every_30s() -> None:
    world = World(world_seed=0)
    _clear_resource_layers(world)
    planted = world.plant_tree(8, 8, now_ms=0, species=1)
    assert planted is not None

    world.update_tree_growth(now_ms=29_999)
    assert planted.stage == TreeStage.SAPLING
    assert planted.can_chop is False

    world.update_tree_growth(now_ms=30_000)
    assert planted.stage == TreeStage.YOUNG

    world.update_tree_growth(now_ms=90_000)
    assert planted.stage == TreeStage.ADULT
    assert planted.can_chop is True


def test_matured_planted_tree_becomes_discoverable_for_lumberjack_search() -> None:
    world = World(world_seed=0)
    _clear_resource_layers(world)
    planted = world.plant_tree(12, 10, now_ms=0, species=0)
    assert planted is not None

    nearest_before = find_nearest_free_tree(world, (10, 10), blocked=set())
    assert nearest_before is None

    world.update_tree_growth(now_ms=90_000)
    nearest_after = find_nearest_free_tree(world, (10, 10), blocked=set())
    assert nearest_after == (12, 10)
