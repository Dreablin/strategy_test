"""Failing tests for forester hiring, assignment, and planting cycle (T155)."""

from __future__ import annotations

from game.buildings.forester_hut import ForesterHut
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.resources import ResourceManager
from game.trees import TreeStage
from game.world import World
from game.workers import Worker, WorkerManager, building_center_tile


def _setup_forester_runtime() -> tuple[list[int], World, BuildingRegistry, ResourceManager, ForesterHut, WorkerManager]:
    now_ms = [0]
    world = World(world_seed=0)
    resources = ResourceManager()
    registry = BuildingRegistry(world)
    th = registry.place(TownHall, town_hall_origin_tile())
    th.level = 10
    hut = registry.place(ForesterHut, near_town_hall_tile(12, 4))
    workers = WorkerManager(resources, registry, now_ms_fn=lambda: now_ms[0])
    return now_ms, world, registry, resources, hut, workers


def test_forester_hiring_and_assignment_only_targets_forester_hut() -> None:
    _, _world, registry, _resources, hut, workers = _setup_forester_runtime()

    forester = workers.hire("FORESTER")
    assert forester is not None
    workers.reassign_all()
    assert forester.assigned_building is hut
    assert forester.idle is False

    other_hut = registry.place(ForesterHut, near_town_hall_tile(18, 8))
    lumberjack = Worker("LUMBERJACK")
    workers.add_worker(lumberjack)
    workers.reassign_all()
    assert lumberjack.assigned_building is not other_hut


def test_forester_selects_reachable_free_tile_within_radius_15() -> None:
    now_ms, world, _registry, _resources, hut, workers = _setup_forester_runtime()
    forester = workers.hire("FORESTER")
    assert forester is not None
    workers.reassign_all()

    now_ms[0] += 120_000
    workers.update(now_ms[0])
    assert forester.target_tile is not None
    tx, ty = forester.target_tile
    hx, hy = building_center_tile(hut)
    assert max(abs(tx - hx), abs(ty - hy)) <= 15
    assert world.is_in_grass(tx, ty)
    assert not world.is_occupied(tx, ty)
    assert world.tree_at(tx, ty) is None
    assert world.stone_at(tx, ty) is None


def test_forester_enters_planting_for_exactly_5000ms_then_plants_sapling() -> None:
    now_ms, world, _registry, _resources, _hut, workers = _setup_forester_runtime()
    forester = workers.hire("FORESTER")
    assert forester is not None
    workers.reassign_all()
    now_ms[0] += 120_000
    workers.update(now_ms[0])
    target = forester.target_tile
    assert target is not None
    tx, ty = target

    assert forester.state == "planting"
    workers.update(now_ms[0] + 4_999)
    assert forester.state == "planting"
    assert world.tree_at(tx, ty) is None

    workers.update(now_ms[0] + 5_000)
    planted = world.tree_at(tx, ty)
    assert planted is not None
    assert planted.stage == TreeStage.SAPLING


def test_inactive_hut_blocks_new_cycle_but_in_progress_planting_finishes() -> None:
    now_ms, world, _registry, _resources, hut, workers = _setup_forester_runtime()
    forester = workers.hire("FORESTER")
    assert forester is not None
    workers.reassign_all()
    now_ms[0] += 120_000
    workers.update(now_ms[0])
    target = forester.target_tile
    assert target is not None

    hut.set_active(False)
    workers.update(now_ms[0] + 5_000)
    assert world.tree_at(*target) is not None
    assert forester.state in {"returning", "working", "idle"}

    before_tile = forester.target_tile
    workers.update(now_ms[0] + 120_000)
    assert forester.target_tile == before_tile or forester.target_tile is None
