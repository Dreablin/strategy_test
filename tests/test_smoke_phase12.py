"""Phase 12 end-to-end smoke tests for stones, stonecutter, and storage/upgrade flow."""

from __future__ import annotations

from game.buildings.lumber_camp import LumberCamp
from game.config import near_town_hall_tile, town_hall_footprint_tiles, town_hall_origin_tile
from game.buildings.registry import BuildingRegistry
from game.buildings.stone_mine import StoneMine
from game.buildings.town_hall import TownHall
from game.stones import Stone
from game.trees import Tree, TreeStage
from game.world import World
from game.workers import MINE_DURATION_MS, WorkerManager


def test_world_boots_with_six_stone_clusters_one_on_th_ring_twenty() -> None:
    world = World()
    centers = world._stone_centers  # noqa: SLF001
    assert len(centers) == 6

    protected = town_hall_footprint_tiles()
    on_ring_20 = [
        (cx, cy)
        for cx, cy in centers
        if min(max(abs(cx - tx), abs(cy - ty)) for tx, ty in protected) == 20
    ]
    assert len(on_ring_20) >= 1
    for cx, cy in centers:
        assert min(max(abs(cx - tx), abs(cy - ty)) for tx, ty in protected) >= 12


def test_stone_mine_placement_rejects_stone_tile_but_accepts_adjacent() -> None:
    world = World()
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    town_hall.level = 3

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
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    town_hall.level = 3
    camp = registry.place(LumberCamp, near_town_hall_tile())
    gx, gy = camp.grid_pos  # type: ignore[assignment]
    for i in range(4):
        world._trees[(gx + 3 + i, gy)] = Tree(stage=TreeStage.ADULT)  # noqa: SLF001
    mine = registry.place(StoneMine, near_town_hall_tile(14, 0))
    mx, my = mine.grid_pos  # type: ignore[assignment]
    world._stones[(mx + 3, my)] = Stone(units=10)  # noqa: SLF001
    world._stones[(mx + 4, my)] = Stone(units=10)  # noqa: SLF001

    now_ms = [0]
    workers = WorkerManager(registry, now_ms_fn=lambda: now_ms[0])
    lumberjack = workers.hire("LUMBERJACK")
    stonecutter = workers.hire("STONECUTTER")
    carrier = workers.hire("CARRIER")
    assert lumberjack is not None
    assert stonecutter is not None
    assert carrier is not None
    workers.reassign_all()

    # Stonecutter: walk -> rest -> go to stone -> mine -> deposit +1 stone.
    wh_stone_before = town_hall.warehouse_amount("stone")
    now_ms[0] += 120_000
    workers.update(now_ms[0])
    assert stonecutter.state in {"going_to_stone", "mining", "returning", "arrived_camp", "depositing", "working"}

    for _ in range(200):
        if stonecutter.state == "mining":
            break
        now_ms[0] += 10_000
        workers.update(now_ms[0])
    assert stonecutter.state == "mining"
    mine.set_active(False)  # Toggle off mid-cycle: current cycle should finish.

    now_ms[0] += MINE_DURATION_MS
    workers.update(now_ms[0])
    now_ms[0] += 120_000
    workers.update(now_ms[0])
    workers.update(now_ms[0] + 1)
    for _ in range(400):
        now_ms[0] += 1_000
        workers.update(now_ms[0])
        if town_hall.warehouse_amount("stone") >= wh_stone_before + 1:
            break
    assert town_hall.warehouse_amount("stone") == wh_stone_before + 1
    assert mine.delivered_stone >= 1
    assert stonecutter.state == "working"
    wait_until = stonecutter.camp_wait_until_ms
    workers.update(wait_until + 200_000)
    assert stonecutter.state == "working"
    assert stonecutter.target_tree is None

    # Lumberjack: upgrade camp and validate gather-speed bonus is applied.
    assert registry.upgrade_building(camp)
    assert camp in registry.all()
    assert lumberjack.characteristics.gather_speed_mult == 1.05

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
