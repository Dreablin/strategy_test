"""Failing tests for Stonecutter active-cycle state machine (T118)."""

from game.buildings.registry import BuildingRegistry
from game.buildings.stone_mine import StoneMine
from game.buildings.town_hall import TownHall
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.stones import Stone
from game.world import World
from game.workers import WorkerManager


def _mine_and_stone_tiles() -> tuple[tuple[int, int], tuple[int, int], tuple[int, int]]:
    """Stone mine position plus two adjacent stone tiles (deterministic layout)."""
    mine_pos = near_town_hall_tile(10, 10)
    s1 = (mine_pos[0] - 2, mine_pos[1] - 2)
    s2 = (mine_pos[0] - 1, mine_pos[1] - 2)
    return mine_pos, s1, s2


def _setup_stonecutter_cycle():
    now_ms = [0]
    world = World()
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    mine_pos, s1, s2 = _mine_and_stone_tiles()
    world._stones[s1] = Stone(units=10)  # noqa: SLF001
    world._stones[s2] = Stone(units=10)  # noqa: SLF001
    resources = None
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    town_hall.level = 3
    mine = registry.place(StoneMine, mine_pos)
    mine.construction_site = None
    workers = WorkerManager(registry, now_ms_fn=lambda: now_ms[0])
    worker = workers.hire("STONECUTTER")
    assert worker is not None
    workers.reassign_all()
    return now_ms, world, resources, registry, mine, workers, worker, s1, s2, town_hall


def test_stonecutter_full_cycle_states_and_carrying_toggle() -> None:
    now_ms, _world, _resources, _registry, _mine, workers, worker, _s1, _s2, _th = _setup_stonecutter_cycle()

    assert worker.state == "moving"
    assert worker.carrying is None

    now_ms[0] += 120_000
    workers.update(now_ms[0])
    assert worker.state in {"going_to_stone", "mining", "returning", "arrived_camp", "depositing", "working"}

    # Once a mining trip completes, stone should be carried on return and
    # cleared again on deposit.
    for _ in range(20):
        now_ms[0] += 20_000
        workers.update(now_ms[0])
        if worker.state in {"returning", "arrived_camp", "depositing"}:
            break
    assert worker.carrying == "stone"

    for _ in range(20):
        now_ms[0] += 20_000
        workers.update(now_ms[0])
        if worker.state == "working":
            break
    assert worker.carrying is None


def test_second_stonecutter_cannot_claim_reserved_stone() -> None:
    now_ms, world, resources, registry, _mine, workers, worker_a, s1, s2, _th = _setup_stonecutter_cycle()
    mine2 = registry.place(StoneMine, near_town_hall_tile(20, 5))
    mine2.construction_site = None
    worker_b = workers.hire("STONECUTTER")
    assert worker_b is not None
    workers.reassign_all()

    now_ms[0] += 120_000
    workers.update(now_ms[0])

    reserved_tiles = [tile for tile, _stone in world.iter_stones() if world.is_stone_reserved(*tile)]
    # Two active stonecutters with two free stones should reserve distinct targets.
    assert len(reserved_tiles) == 2


def test_demolish_stone_mine_mid_cycle_cancels_worker_activity() -> None:
    now_ms, world, resources, registry, mine, workers, worker, s1, s2, town_hall = _setup_stonecutter_cycle()

    now_ms[0] += 120_000
    workers.update(now_ms[0])
    assert worker.state in {"going_to_stone", "mining", "returning", "arrived_camp", "depositing"}
    stone_before = town_hall.warehouse_amount("stone")

    registry.demolish(mine, workers)
    assert worker.state == "idle"
    assert worker.carrying is None

    now_ms[0] += 240_000
    workers.update(now_ms[0])
    assert town_hall.warehouse_amount("stone") == stone_before
    assert world.is_stone_reserved(*s1) is False
    assert world.is_stone_reserved(*s2) is False


def test_stonecutter_skips_unminable_nearest_stone_and_targets_next() -> None:
    now_ms = [0]
    world = World()
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    mine_pos, blocked_stone, _ = _mine_and_stone_tiles()
    world._stones[blocked_stone] = Stone(units=10)  # noqa: SLF001
    for t in [
        (blocked_stone[0] - 1, blocked_stone[1] - 1),
        (blocked_stone[0], blocked_stone[1] - 1),
        (blocked_stone[0] + 1, blocked_stone[1] - 1),
        (blocked_stone[0] - 1, blocked_stone[1]),
        (blocked_stone[0] + 1, blocked_stone[1]),
        (blocked_stone[0] - 1, blocked_stone[1] + 1),
        (blocked_stone[0], blocked_stone[1] + 1),
        (blocked_stone[0] + 1, blocked_stone[1] + 1),
    ]:
        world.mark_occupied(t[0], t[1], 1, 1)
    far_stone = (blocked_stone[0] + 4, blocked_stone[1] + 4)
    world._stones[far_stone] = Stone(units=10)  # noqa: SLF001

    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile()).level = 3
    mine = registry.place(StoneMine, mine_pos)
    mine.construction_site = None
    workers = WorkerManager(registry, now_ms_fn=lambda: now_ms[0])
    worker = workers.hire("STONECUTTER")
    assert worker is not None
    workers.reassign_all()

    now_ms[0] = 120_000
    workers.update(now_ms[0])
    assert worker.assigned_building is mine
    assert worker.state in {"going_to_stone", "mining", "returning", "arrived_camp", "depositing", "working"}
    assert worker.target_tree == far_stone
