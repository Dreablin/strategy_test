"""Equivalence guard: cached blocked tiles equals legacy full-grid union (T130)."""

from game.buildings.lumber_camp import LumberCamp
from game.config import town_hall_origin_tile
from game.buildings.registry import BuildingRegistry
from game.buildings.stone_mine import StoneMine
from game.buildings.town_hall import TownHall
from game.stones import Stone
from game.trees import Tree, TreeStage
from game.world import World
from game.workers import WorkerManager


def _legacy_blocked(world: World) -> set[tuple[int, int]]:
    occupied = {
        (x, y)
        for y in range(world.height)
        for x in range(world.width)
        if world.is_occupied(x, y)
    }
    trees = {tile for tile, _tree in world.iter_alive_trees()}
    stones = {tile for tile, _stone in world.iter_stones()}
    return occupied | trees | stones | world.iron_blocking_tiles() | world.gold_blocking_tiles()


def test_blocked_tiles_matches_legacy_scan_across_world_mutations() -> None:
    world = World()
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    world._iron.clear()  # noqa: SLF001
    world._gold.clear()  # noqa: SLF001
    world._trees[(8, 8)] = Tree(stage=TreeStage.ADULT)  # noqa: SLF001
    world._trees[(9, 8)] = Tree(stage=TreeStage.ADULT)  # noqa: SLF001
    world._stones[(12, 12)] = Stone(units=1)  # noqa: SLF001
    world._stones[(13, 12)] = Stone(units=2)  # noqa: SLF001

    registry = BuildingRegistry(world)
    workers = WorkerManager(registry)
    th = registry.place(TownHall, town_hall_origin_tile())
    th.level = 3
    camp_a = registry.place(LumberCamp, (20, 20))
    _mine = registry.place(StoneMine, (24, 20))

    assert world.blocked_tiles() == _legacy_blocked(world)

    camp_b = registry.place(LumberCamp, (28, 20))
    assert camp_b is not None
    assert world.blocked_tiles() == _legacy_blocked(world)

    registry.demolish(camp_a, workers)
    assert world.blocked_tiles() == _legacy_blocked(world)

    world.harvest_stone(12, 12)  # depleted and removed
    assert world.blocked_tiles() == _legacy_blocked(world)

    world.remove_tree(8, 8)
    assert world.blocked_tiles() == _legacy_blocked(world)
