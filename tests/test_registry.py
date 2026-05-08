"""Tests for BuildingRegistry placement rules and occupancy."""

import math

import pytest

from game.buildings.lumber_camp import LumberCamp
from game.buildings.chicken_farm import ChickenFarm
from game.buildings.iron_mine import IronMine
from game.buildings.stone_mine import StoneMine
from game.buildings.sawmill import Sawmill
from game.buildings.mill import Mill
from game.buildings.town_hall import TownHall
from game.buildings.registry import BuildingRegistry
from game.config import CONSTRUCTION_REQUIREMENTS, GRID_SIZE, near_town_hall_tile, town_hall_origin_tile
from game.iron import IronDeposit
from game.world import World
from game.workers import Worker, WorkerManager


@pytest.fixture
def world() -> World:
    # Fixed seed: placements in these tests assume specific grass tiles stay free of proc stones/trees.
    return World(world_seed=0)


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
    assert not registry.can_place(LumberCamp, (GRID_SIZE - 1, 0))
    assert not registry.can_place(LumberCamp, (0, GRID_SIZE - 1))


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
    assert registry.can_place(TownHall, town_hall_origin_tile())
    registry.place(TownHall, town_hall_origin_tile())
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
    th = registry.place(TownHall, town_hall_origin_tile())
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
    th = registry.place(TownHall, town_hall_origin_tile())
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


def test_stone_mine_does_not_require_town_hall_upgrade_level(registry: BuildingRegistry) -> None:
    th = registry.place(TownHall, town_hall_origin_tile())
    assert th.level == 1
    assert registry.can_place(StoneMine, (8, 8))


def test_iron_mine_does_not_require_town_hall_upgrade_level(registry: BuildingRegistry) -> None:
    th = registry.place(TownHall, town_hall_origin_tile())
    assert th.level == 1
    registry._world._iron.clear()  # noqa: SLF001
    registry._world._iron[(8, 8)] = IronDeposit(blocking=False)  # noqa: SLF001
    assert registry.can_place(IronMine, (8, 8))


def test_can_place_allows_footprint_with_trees_present(registry: BuildingRegistry, world: World) -> None:
    from game.trees import Tree, TreeStage

    if world.tree_at(10, 10) is None:
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


def test_place_lumber_camp_starts_under_construction_with_level1_requirements(
    registry: BuildingRegistry,
) -> None:
    camp = registry.place(LumberCamp, (10, 10))
    assert camp.is_under_construction
    assert camp.construction_site is not None
    expected = CONSTRUCTION_REQUIREMENTS["LUMBER_CAMP"][1]
    assert camp.construction_site.required_resources == expected.cost


def test_place_town_hall_has_no_construction_site(registry: BuildingRegistry) -> None:
    th = registry.place(TownHall, town_hall_origin_tile())
    assert th.is_under_construction is False
    assert th.construction_site is None


def test_place_sawmill_starts_under_construction_with_level1_requirements(
    registry: BuildingRegistry,
) -> None:
    sawmill = registry.place(Sawmill, (16, 16))
    assert sawmill.is_under_construction
    assert sawmill.construction_site is not None
    expected = CONSTRUCTION_REQUIREMENTS["SAWMILL"][1]
    assert sawmill.construction_site.required_resources == expected.cost


def test_upgrade_sawmill_starts_construction_for_level2() -> None:
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    sawmill = registry.place(Sawmill, (22, 22))
    sawmill.construction_site = None

    assert registry.upgrade_building(sawmill)
    assert sawmill.level == 1
    assert sawmill.is_under_construction
    assert sawmill.construction_site is not None
    assert sawmill.construction_site.target_level == 2


def test_place_mill_starts_under_construction_with_level1_requirements(
    registry: BuildingRegistry,
) -> None:
    mill = registry.place(Mill, (24, 16))
    assert mill.is_under_construction
    assert mill.construction_site is not None
    expected = CONSTRUCTION_REQUIREMENTS["MILL"][1]
    assert mill.construction_site.required_resources == expected.cost


def test_upgrade_mill_starts_construction_for_level2() -> None:
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    mill = registry.place(Mill, (24, 22))
    mill.construction_site = None

    assert registry.upgrade_building(mill)
    assert mill.level == 1
    assert mill.is_under_construction
    assert mill.construction_site is not None
    assert mill.construction_site.target_level == 2


def test_cannot_place_when_footprint_covers_stone_tile() -> None:
    from game.stones import Stone

    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    world._stones[(10, 10)] = Stone()  # noqa: SLF001
    assert not registry.can_place(LumberCamp, (10, 10))


def test_rejected_place_does_not_remove_stones_in_footprint() -> None:
    from game.stones import Stone

    world = World(world_seed=2)
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    world._stones[(10, 10)] = Stone()  # noqa: SLF001
    with pytest.raises(ValueError):
        registry.place(LumberCamp, (10, 10))
    assert world.stone_at(10, 10) is not None


def test_upgrade_keeps_building_in_registry_list() -> None:
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    camp = registry.place(LumberCamp, (12, 12))
    camp.construction_site = None

    assert registry.upgrade_building(camp)
    assert camp in registry.all()
    assert camp.level == 1
    assert camp.is_under_construction
    assert camp.construction_site is not None
    assert camp.construction_site.target_level == 2


def test_upgrade_assigned_worker_transitions_to_resting_inside_building() -> None:
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    camp = registry.place(LumberCamp, (14, 14))
    camp.construction_site = None
    workers = WorkerManager(registry)
    worker = Worker("LUMBERJACK")
    workers.add_worker(worker)
    workers.assign_to_building(worker, camp)

    assert registry.upgrade_building(camp)
    assert worker.assigned_building is camp
    assert worker.idle is False
    assert worker.state == "resting"
    assert worker.current_tile == (15, 15)


def test_upgrade_pauses_active_building_and_releases_worker_outside_footprint() -> None:
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    camp = registry.place(LumberCamp, (14, 14))
    camp.construction_site = None
    workers = WorkerManager(registry)
    worker = Worker("LUMBERJACK")
    workers.add_worker(worker)
    workers.assign_to_building(worker, camp)
    worker.state = "going_to_tree"
    worker.current_tile = (20, 20)

    assert camp.active is True
    assert registry.upgrade_building(camp)

    assert camp.active is False
    assert worker.assigned_building is None
    assert worker.idle is True
    assert worker.state == "idle"
    assert worker.current_tile == (20, 20)
    assert worker.stand_tile == (20, 20)
    assert camp.construction_site is not None
    assert camp.construction_site.resting_worker is None


def test_upgrade_does_not_teleport_worker_walking_to_newly_built_workplace() -> None:
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    farm = registry.place(ChickenFarm, near_town_hall_tile(18, 8))
    farm.construction_site = None
    workers = WorkerManager(registry)
    registry.bind_worker_manager(workers)
    worker = Worker("ANIMAL_HERDER", stand_tile=(8, 8))
    workers.add_worker(worker)
    worker.assigned_building = farm
    worker.state = "moving"
    worker.idle = False
    worker.current_tile = (8, 8)
    worker.stand_tile = (8, 8)
    worker.target_tile = (9, 8)
    worker.path = [(8, 8), (9, 8), (10, 8)]
    worker.segment_progress = 0.25

    assert registry.upgrade_building(farm)

    assert farm.construction_site is not None
    assert farm.construction_site.resting_worker is None
    assert worker.assigned_building is None
    assert worker.idle is True
    assert worker.state == "idle"
    assert worker.current_tile == (8, 8)
    assert worker.target_tile is None
    assert worker.path == []


def test_upgrade_rejected_while_building_already_under_construction() -> None:
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    camp = registry.place(LumberCamp, (18, 18))
    camp.construction_site = None
    assert registry.upgrade_building(camp)
    assert camp.is_under_construction
    assert not registry.upgrade_building(camp)


def test_demolish_after_upgrade_construction_still_clears_worker_assignment() -> None:
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    camp = registry.place(LumberCamp, near_town_hall_tile())
    camp.construction_site = None
    workers = WorkerManager(registry)
    worker = Worker("LUMBERJACK")
    workers.add_worker(worker)
    workers.assign_to_building(worker, camp)

    assert registry.upgrade_building(camp)
    assert camp.is_under_construction

    registry.demolish(camp, workers)
    assert worker.assigned_building is None
    assert worker.idle
