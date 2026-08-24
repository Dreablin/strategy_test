"""Tests for generated gold edge deposits."""

from game.buildings.lumber_camp import LumberCamp
from game.buildings.registry import BuildingRegistry
from game.config import GRID_SIZE
from game.gold import GoldDeposit
from game.world import World


def test_world_generates_one_gold_zone_near_map_edge() -> None:
    world = World(world_seed=7)
    center = world._gold_center  # noqa: SLF001

    assert center is not None
    assert world.gold_tiles()
    assert min(center[0], center[1], GRID_SIZE - 1 - center[0], GRID_SIZE - 1 - center[1]) <= 17


def test_world_generates_single_gold_zone() -> None:
    world = World(world_seed=7)
    center = world._gold_center  # noqa: SLF001

    assert center is not None
    assert all(
        max(abs(tile[0] - center[0]), abs(tile[1] - center[1])) <= 6
        for tile in world.gold_tiles()
    )


def test_gold_deposits_have_blocking_core_and_buildable_fragments() -> None:
    world = World(world_seed=7)

    blocking = world.gold_blocking_tiles()
    buildable = world.gold_buildable_tiles()
    assert blocking
    assert buildable
    assert blocking.isdisjoint(buildable)
    assert blocking <= world.blocked_tiles()
    assert buildable.isdisjoint(world.blocked_tiles())
    assert all(0 <= gold.variant <= 4 for _tile, gold in world.iter_gold_deposits())


def test_buildable_gold_continues_directly_from_blocking_core() -> None:
    world = World(world_seed=7)
    blocking = world.gold_blocking_tiles()
    buildable = world.gold_buildable_tiles()

    assert any(
        any(
            (tile[0] + dx, tile[1] + dy) in blocking
            for dx in (-1, 0, 1)
            for dy in (-1, 0, 1)
            if dx != 0 or dy != 0
        )
        for tile in buildable
    )


def test_other_world_resources_do_not_spawn_on_gold() -> None:
    world = World(world_seed=7)

    gold = world.gold_tiles()
    assert gold.isdisjoint(world.iron_tiles())
    assert gold.isdisjoint(world.stone_tiles())
    assert gold.isdisjoint(world.tree_tiles())


def test_trees_cannot_be_planted_on_any_gold_tile() -> None:
    world = World(world_seed=2)
    buildable = next(iter(world.gold_buildable_tiles()))
    blocking = next(iter(world.gold_blocking_tiles()))

    assert world.plant_tree(*buildable, now_ms=0) is None
    assert world.plant_tree(*blocking, now_ms=0) is None


def test_regular_buildings_cannot_be_placed_on_gold() -> None:
    world = World(world_seed=2)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    world._iron.clear()  # noqa: SLF001
    world._gold.clear()  # noqa: SLF001
    world._gold[(20, 20)] = GoldDeposit(blocking=False)  # noqa: SLF001
    registry = BuildingRegistry(world)

    assert not registry.can_place(LumberCamp, (20, 20))
