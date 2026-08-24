"""Tests for generated iron rifts and buildable ore fragments."""

from game.buildings.iron_mine import IronMine
from game.buildings.lumber_camp import LumberCamp
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.config import WORLD_IRON_ZONE_COUNT, town_hall_footprint_tiles, town_hall_origin_tile
from game.iron import IronDeposit
from game.world import World


def _min_chebyshev_to_town_hall(tile: tuple[int, int]) -> int:
    tx, ty = tile
    return min(max(abs(tx - hx), abs(ty - hy)) for hx, hy in town_hall_footprint_tiles())


def test_world_generates_two_iron_zones_with_near_and_far_centers() -> None:
    world = World(world_seed=7)
    centers = list(world._iron_centers)  # noqa: SLF001

    assert len(centers) == WORLD_IRON_ZONE_COUNT
    assert _min_chebyshev_to_town_hall(centers[0]) == 30
    assert any(_min_chebyshev_to_town_hall(center) > 30 for center in centers[1:])


def test_iron_deposits_have_blocking_core_and_buildable_fragments() -> None:
    world = World(world_seed=7)

    blocking = world.iron_blocking_tiles()
    buildable = world.iron_buildable_tiles()
    assert blocking
    assert buildable
    assert blocking.isdisjoint(buildable)
    assert blocking <= world.blocked_tiles()
    assert buildable.isdisjoint(world.blocked_tiles())
    assert all(0 <= iron.variant <= 4 for _tile, iron in world.iter_iron_deposits())


def test_buildable_iron_continues_directly_from_blocking_core() -> None:
    world = World(world_seed=7)
    blocking = world.iron_blocking_tiles()
    buildable = world.iron_buildable_tiles()

    adjacent_to_core = {
        tile
        for tile in buildable
        if any(
            (tile[0] + dx, tile[1] + dy) in blocking
            for dx in (-1, 0, 1)
            for dy in (-1, 0, 1)
            if dx != 0 or dy != 0
        )
    }
    assert adjacent_to_core
    assert all(
        any(
            (tile[0] + dx, tile[1] + dy) in blocking or (tile[0] + dx, tile[1] + dy) in buildable
            for dx in (-1, 0, 1)
            for dy in (-1, 0, 1)
            if dx != 0 or dy != 0
        )
        for tile in buildable
    )


def test_stones_and_trees_do_not_spawn_on_iron() -> None:
    world = World(world_seed=7)

    iron = world.iron_tiles()
    assert iron.isdisjoint(world.stone_tiles())
    assert iron.isdisjoint(world.tree_tiles())


def test_iron_generation_is_seed_reproducible() -> None:
    first = World(world_seed=11)
    second = World(world_seed=11)

    first_state = sorted((tile, iron.blocking, iron.variant) for tile, iron in first.iter_iron_deposits())
    second_state = sorted((tile, iron.blocking, iron.variant) for tile, iron in second.iter_iron_deposits())
    assert first_state == second_state


def test_trees_cannot_be_planted_on_any_iron_tile() -> None:
    world = World(world_seed=2)
    buildable = next(iter(world.iron_buildable_tiles()))
    blocking = next(iter(world.iron_blocking_tiles()))

    assert world.plant_tree(*buildable, now_ms=0) is None
    assert world.plant_tree(*blocking, now_ms=0) is None


def test_only_iron_mine_can_be_placed_on_buildable_iron() -> None:
    world = World(world_seed=2)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    world._iron.clear()  # noqa: SLF001
    world._iron[(20, 20)] = IronDeposit(blocking=False)  # noqa: SLF001
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())

    assert registry.can_place(IronMine, (20, 20))
    assert not registry.can_place(LumberCamp, (20, 20))


def test_iron_mine_requires_buildable_iron_and_avoids_blocking_iron() -> None:
    world = World(world_seed=2)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    world._iron.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())

    assert not registry.can_place(IronMine, (20, 20))

    world._iron[(20, 20)] = IronDeposit(blocking=True)  # noqa: SLF001
    assert not registry.can_place(IronMine, (20, 20))
