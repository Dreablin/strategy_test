"""Tests for BuildingRegistry placement rules and occupancy."""

import math

import pytest

from game.buildings.lumber_camp import LumberCamp
from game.buildings.iron_mine import IronMine
from game.buildings.stone_mine import StoneMine
from game.buildings.town_hall import TownHall
from game.buildings.registry import BuildingRegistry
from game.resources import ResourceManager
from game.world import World
from game.workers import Worker, WorkerManager


@pytest.fixture
def world() -> World:
    return World()


@pytest.fixture
def registry(world: World) -> BuildingRegistry:
    return BuildingRegistry(world)


def _min_chebyshev_between_footprints(
    ax: int, ay: int, aw: int, ah: int, bx: int, by: int, bw: int, bh: int
) -> int:
    best = 10**9
    for gx in range(ax, ax + aw):
        for gy in range(ay, ay + ah):
            for gx2 in range(bx, bx + bw):
                for gy2 in range(by, by + bh):
                    d = max(abs(gx - gx2), abs(gy - gy2))
                    best = min(best, d)
    return best


def test_cannot_place_footprint_outside_grass(registry: BuildingRegistry) -> None:
    assert not registry.can_place(LumberCamp, (54, 0))
    assert not registry.can_place(LumberCamp, (0, 54))


def test_cannot_place_overlapping_buildings(registry: BuildingRegistry) -> None:
    assert registry.can_place(LumberCamp, (10, 10))
    registry.place(LumberCamp, (10, 10))
    assert not registry.can_place(StoneMine, (10, 10))
    assert not registry.can_place(StoneMine, (11, 11))


def test_distance_rule_uses_new_building_max_footprint(registry: BuildingRegistry) -> None:
    """F-PLACE-03: reject when min Chebyshev gap < ceil(0.5 * max(new_w, new_h))."""
    registry.place(LumberCamp, (10, 10))
    lw, lh = LumberCamp.footprint
    sep = math.ceil(0.5 * max(TownHall.footprint))

    bad_x, bad_y = 12, 12
    assert (
        _min_chebyshev_between_footprints(
            bad_x, bad_y, *TownHall.footprint, 10, 10, lw, lh
        )
        < sep
    )
    assert not registry.can_place(TownHall, (bad_x, bad_y))

    good_x, good_y = 13, 13
    assert (
        _min_chebyshev_between_footprints(
            good_x, good_y, *TownHall.footprint, 10, 10, lw, lh
        )
        >= sep
    )
    assert registry.can_place(TownHall, (good_x, good_y))


def test_second_town_hall_always_rejected(registry: BuildingRegistry) -> None:
    assert registry.can_place(TownHall, (16, 16))
    registry.place(TownHall, (16, 16))
    assert not registry.can_place(TownHall, (0, 0))
    assert not registry.can_place(TownHall, (10, 10))


def test_demolish_clears_world_occupancy(registry: BuildingRegistry, world: World) -> None:
    registry.place(LumberCamp, (5, 5))
    assert world.is_occupied(5, 5)
    b = registry.at(5, 5)
    assert b is not None
    registry.demolish(b)
    assert registry.at(5, 5) is None
    assert not world.is_occupied(5, 5)


def test_demolish_with_worker_manager_notifies_before_removal(registry: BuildingRegistry) -> None:
    camp = registry.place(LumberCamp, (12, 12))
    wm = WorkerManager()
    w = Worker("LUMBERJACK")
    wm.add_worker(w)
    wm.assign_to_building(w, camp)
    registry.demolish(camp, wm)
    assert camp not in registry.all()
    assert w.idle
    assert w.stand_tile == (13, 13)


def test_all_lists_placed_buildings(registry: BuildingRegistry) -> None:
    th = registry.place(TownHall, (16, 16))
    th.level = 3
    registry.place(LumberCamp, (4, 4))
    registry.place(StoneMine, (20, 20))
    all_b = registry.all()
    assert len(all_b) == 3


def test_adjacent_edge_touch_rejected(registry: BuildingRegistry) -> None:
    registry.place(LumberCamp, (10, 10))
    # Right next to 2x2 footprint: new starts at x=12 touches edge.
    assert not registry.can_place(StoneMine, (12, 10))


def test_adjacent_corner_touch_rejected(registry: BuildingRegistry) -> None:
    registry.place(LumberCamp, (10, 10))
    # Corner-touch at (12,12) for two 2x2 footprints.
    assert not registry.can_place(StoneMine, (12, 12))


def test_exactly_one_tile_gap_accepted(registry: BuildingRegistry) -> None:
    th = registry.place(TownHall, (16, 16))
    th.level = 3
    registry.place(LumberCamp, (10, 10))
    # One tile horizontal gap between footprints.
    assert registry.can_place(StoneMine, (13, 10))


def test_town_hall_and_resource_use_same_spacing_rule(registry: BuildingRegistry) -> None:
    registry.place(TownHall, (10, 10))
    # Touching edge at x=13 should be rejected.
    assert not registry.can_place(LumberCamp, (13, 11))
    # One-tile gap at x=14 should be accepted.
    assert registry.can_place(LumberCamp, (14, 11))


def test_stone_mine_requires_town_hall_level_3(registry: BuildingRegistry) -> None:
    th = registry.place(TownHall, (16, 16))
    assert not registry.can_place(StoneMine, (8, 8))
    th.level = 3
    assert registry.can_place(StoneMine, (8, 8))


def test_iron_mine_requires_town_hall_level_5(registry: BuildingRegistry) -> None:
    th = registry.place(TownHall, (16, 16))
    assert not registry.can_place(IronMine, (8, 8))
    th.level = 4
    assert not registry.can_place(IronMine, (8, 8))
    th.level = 5
    assert registry.can_place(IronMine, (8, 8))


def test_can_place_allows_footprint_with_trees_present(registry: BuildingRegistry, world: World) -> None:
    world._trees[(10, 10)] = world._trees.get((10, 10)) or world.tree_at(0, 0)  # noqa: SLF001
    if world._trees[(10, 10)] is None:  # noqa: SLF001
        from game.trees import Tree, TreeStage

        world._trees[(10, 10)] = Tree(stage=TreeStage.YOUNG)  # noqa: SLF001
    assert registry.can_place(LumberCamp, (10, 10))


def test_place_clears_trees_inside_building_footprint(registry: BuildingRegistry, world: World) -> None:
    from game.trees import Tree, TreeStage

    for tile in [(10, 10), (11, 10), (10, 11), (11, 11)]:
        world._trees[tile] = Tree(stage=TreeStage.ADULT)  # noqa: SLF001
        assert world.is_tree_blocking(*tile)

    placed = registry.place(LumberCamp, (10, 10))
    assert placed is not None
    for tile in [(10, 10), (11, 10), (10, 11), (11, 11)]:
        assert not world.is_tree_blocking(*tile)
        assert world.tree_at(*tile) is None


def test_tree_presence_does_not_bypass_overlap_or_spacing_rules(
    registry: BuildingRegistry, world: World
) -> None:
    from game.trees import Tree, TreeStage

    world._trees[(10, 10)] = Tree(stage=TreeStage.MATURE)  # noqa: SLF001
    first = registry.place(LumberCamp, (10, 10))
    assert first is not None
    assert not registry.can_place(StoneMine, (10, 10))
    assert not registry.can_place(StoneMine, (12, 10))


def test_cannot_place_when_footprint_covers_stone_tile() -> None:
    from game.stones import Stone

    world = World()
    registry = BuildingRegistry(world)
    world._stones[(10, 10)] = Stone()  # noqa: SLF001
    assert not registry.can_place(LumberCamp, (10, 10))


def test_place_does_not_remove_stones_in_footprint() -> None:
    from game.stones import Stone

    world = World()
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    world._stones[(10, 10)] = Stone()  # noqa: SLF001
    placed = registry.place(LumberCamp, (10, 10))
    assert placed is not None
    assert world.stone_at(10, 10) is not None


def test_upgrade_keeps_building_in_registry_list() -> None:
    world = World()
    registry = BuildingRegistry(world)
    resources = ResourceManager()
    camp = registry.place(LumberCamp, (12, 12))

    assert registry.upgrade_building(camp, resources)
    assert camp in registry.all()


def test_upgrade_refreshes_assigned_worker_gather_speed_bonus() -> None:
    world = World()
    registry = BuildingRegistry(world)
    resources = ResourceManager()
    camp = registry.place(LumberCamp, (14, 14))
    workers = WorkerManager(resources, registry)
    worker = Worker("LUMBERJACK")
    workers.add_worker(worker)
    workers.assign_to_building(worker, camp)
    assert worker.characteristics.gather_speed_mult == pytest.approx(1.0)

    assert registry.upgrade_building(camp, resources)
    assert worker.characteristics.gather_speed_mult == pytest.approx(1.05)


def test_consecutive_upgrades_stack_additively_for_assigned_worker() -> None:
    world = World()
    registry = BuildingRegistry(world)
    resources = ResourceManager()
    camp = registry.place(LumberCamp, (18, 18))
    workers = WorkerManager(resources, registry)
    worker = Worker("LUMBERJACK")
    workers.add_worker(worker)
    workers.assign_to_building(worker, camp)

    assert registry.upgrade_building(camp, resources)
    assert registry.upgrade_building(camp, resources)
    assert worker.characteristics.move_speed_mult == pytest.approx(1.10)
    assert worker.characteristics.gather_speed_mult == pytest.approx(1.10)


def test_demolish_after_upgrades_clears_move_and_gather_bonus_sources() -> None:
    world = World()
    registry = BuildingRegistry(world)
    resources = ResourceManager()
    camp = registry.place(LumberCamp, (22, 22))
    workers = WorkerManager(resources, registry)
    worker = Worker("LUMBERJACK")
    workers.add_worker(worker)
    workers.assign_to_building(worker, camp)

    assert registry.upgrade_building(camp, resources)
    assert registry.upgrade_building(camp, resources)
    assert worker.characteristics.move_speed_mult == pytest.approx(1.10)
    assert worker.characteristics.gather_speed_mult == pytest.approx(1.10)

    registry.demolish(camp, workers)
    assert worker.characteristics.move_speed_mult == pytest.approx(1.0)
    assert worker.characteristics.gather_speed_mult == pytest.approx(1.0)
