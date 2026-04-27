"""Phase 12 end-to-end smoke tests for stones, stonecutter, and storage/upgrade flow."""

from __future__ import annotations

from game.buildings.lumber_camp import LumberCamp
from game.buildings.registry import BuildingRegistry
from game.buildings.stone_mine import StoneMine
from game.buildings.town_hall import TownHall
from game.resources import ResourceManager
from game.stones import Stone
from game.trees import Tree, TreeStage
from game.world import World
from game.workers import CHOP_DURATION_MS, MINE_DURATION_MS, WorkerManager


def test_world_boots_with_three_stone_clusters_far_from_town_hall_zone() -> None:
    world = World()
    centers = world._stone_centers  # noqa: SLF001
    assert len(centers) == 3

    protected = {(x, y) for y in range(16, 19) for x in range(16, 19)}
    for cx, cy in centers:
        assert min(max(abs(cx - tx), abs(cy - ty)) for tx, ty in protected) >= 12


def test_stone_mine_placement_rejects_stone_tile_but_accepts_adjacent() -> None:
    world = World()
    registry = BuildingRegistry(world)
    registry.place(TownHall, (16, 16)).level = 3

    stone_tile, _stone = world.iter_stones()[0]
    sx, sy = stone_tile
    assert registry.can_place(StoneMine, (sx, sy)) is False

    placed = None
    for y in range(sy - 4, sy + 5):
        for x in range(sx - 4, sx + 5):
            if not registry.can_place(StoneMine, (x, y)):
                continue
            bx, by = x, y
            adjacent = False
            for fy in range(by, by + 2):
                for fx in range(bx, bx + 2):
                    if max(abs(fx - sx), abs(fy - sy)) == 1:
                        adjacent = True
                        break
                if adjacent:
                    break
            if adjacent:
                placed = registry.place(StoneMine, (x, y))
                break
        if placed is not None:
            break

    assert placed is not None
    assert placed.type_tag == "STONE_MINE"


def test_stonecutter_cycle_toggle_upgrade_and_storage_smoke() -> None:
    # Deterministic resources around camps for an end-to-end cycle check.
    world = World()
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    world._trees[(24, 20)] = Tree(stage=TreeStage.ADULT)  # noqa: SLF001
    world._trees[(25, 20)] = Tree(stage=TreeStage.ADULT)  # noqa: SLF001
    world._trees[(26, 20)] = Tree(stage=TreeStage.ADULT)  # noqa: SLF001
    world._trees[(27, 20)] = Tree(stage=TreeStage.ADULT)  # noqa: SLF001
    world._stones[(30, 20)] = Stone(units=10)  # noqa: SLF001
    world._stones[(31, 20)] = Stone(units=10)  # noqa: SLF001

    resources = ResourceManager()
    registry = BuildingRegistry(world)
    registry.place(TownHall, (16, 16)).level = 3
    camp = registry.place(LumberCamp, (22, 22))
    mine = registry.place(StoneMine, (28, 22))

    now_ms = [0]
    workers = WorkerManager(resources, registry, now_ms_fn=lambda: now_ms[0])
    lumberjack = workers.hire("LUMBERJACK")
    stonecutter = workers.hire("STONECUTTER")
    assert lumberjack is not None
    assert stonecutter is not None
    workers.reassign_all()

    # Stonecutter: walk -> rest -> go to stone -> mine -> deposit +1 stone.
    stone_before = resources.get("stone")
    now_ms[0] += 120_000
    workers.update(now_ms[0])
    assert stonecutter.state in {"going_to_stone", "mining", "returning", "arrived_camp", "depositing", "working"}

    while stonecutter.state != "mining":
        now_ms[0] += 10_000
        workers.update(now_ms[0])
    mine.set_active(False)  # Toggle off mid-cycle: current cycle should finish.

    now_ms[0] += MINE_DURATION_MS
    workers.update(now_ms[0])
    now_ms[0] += 120_000
    workers.update(now_ms[0])
    workers.update(now_ms[0] + 1)
    assert resources.get("stone") == stone_before + 1
    assert mine.delivered_stone >= 1
    assert stonecutter.state == "working"
    wait_until = stonecutter.camp_wait_until_ms
    workers.update(wait_until + 200_000)
    assert stonecutter.state == "working"
    assert stonecutter.target_tree is None

    # Lumberjack: upgrade camp mid-cycle, keep building alive, apply 1.05 gather bonus,
    # then next chop snapshot should be CHOP_DURATION_MS / 1.05.
    resources.add("wood", 10_000)
    resources.add("stone", 10_000)
    while lumberjack.state != "chopping":
        now_ms[0] += 10_000
        workers.update(now_ms[0])
    first_chop_started = lumberjack.chop_started_ms
    assert registry.upgrade_building(camp, resources)
    assert camp in registry.all()
    assert lumberjack.characteristics.gather_speed_mult == 1.05

    now_ms[0] += CHOP_DURATION_MS
    workers.update(now_ms[0])
    now_ms[0] += 120_000
    workers.update(now_ms[0])
    workers.update(now_ms[0] + 1)
    while lumberjack.state != "chopping" or lumberjack.chop_started_ms <= first_chop_started:
        now_ms[0] += 10_000
        workers.update(now_ms[0])
    assert lumberjack.chop_duration_ms == int(round(CHOP_DURATION_MS / 1.05))

    # Storage-full gate: no new cycle starts until storage decreases.
    camp.stored = camp.storage_capacity()
    lumberjack.state = "working"
    lumberjack.camp_wait_until_ms = now_ms[0] + 1
    workers.update(now_ms[0] + 500_000)
    assert lumberjack.state == "working"
    workers.update(now_ms[0] + 505_000)
    assert lumberjack.state == "working"

    camp.take_from_storage(1)
    workers.update(now_ms[0] + 510_000)
    assert lumberjack.state in {"going_to_tree", "chopping", "returning", "arrived_camp", "depositing", "working"}
