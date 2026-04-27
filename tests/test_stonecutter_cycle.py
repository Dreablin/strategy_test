"""Failing tests for Stonecutter active-cycle state machine (T118)."""

from game.buildings.registry import BuildingRegistry
from game.buildings.stone_mine import StoneMine
from game.buildings.town_hall import TownHall
from game.resources import ResourceManager
from game.stones import Stone
from game.world import World
from game.workers import WorkerManager


def _setup_stonecutter_cycle():
    now_ms = [0]
    world = World()
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    world._stones[(20, 20)] = Stone(units=10)  # noqa: SLF001
    world._stones[(21, 20)] = Stone(units=10)  # noqa: SLF001
    resources = ResourceManager()
    registry = BuildingRegistry(world)
    registry.place(TownHall, (16, 16)).level = 3
    mine = registry.place(StoneMine, (22, 22))
    workers = WorkerManager(resources, registry, now_ms_fn=lambda: now_ms[0])
    worker = workers.hire("STONECUTTER")
    assert worker is not None
    workers.reassign_all()
    return now_ms, world, resources, registry, mine, workers, worker


def test_stonecutter_full_cycle_states_and_carrying_toggle() -> None:
    now_ms, _world, _resources, _registry, _mine, workers, worker = _setup_stonecutter_cycle()

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
    now_ms, world, resources, registry, _mine, workers, worker_a = _setup_stonecutter_cycle()
    registry.place(StoneMine, (26, 22))
    worker_b = workers.hire("STONECUTTER")
    assert worker_b is not None
    workers.reassign_all()

    now_ms[0] += 120_000
    workers.update(now_ms[0])

    reserved_tiles = [tile for tile, _stone in world.iter_stones() if world.is_stone_reserved(*tile)]
    # Two active stonecutters with two free stones should reserve distinct targets.
    assert len(reserved_tiles) == 2


def test_demolish_stone_mine_mid_cycle_cancels_worker_activity() -> None:
    now_ms, world, resources, registry, mine, workers, worker = _setup_stonecutter_cycle()

    now_ms[0] += 120_000
    workers.update(now_ms[0])
    assert worker.state in {"going_to_stone", "mining", "returning", "arrived_camp", "depositing"}
    stone_before = resources.get("stone")

    registry.demolish(mine, workers)
    assert worker.state == "idle"
    assert worker.carrying is None

    now_ms[0] += 240_000
    workers.update(now_ms[0])
    assert resources.get("stone") == stone_before
    assert world.is_stone_reserved(20, 20) is False
    assert world.is_stone_reserved(21, 20) is False


def test_stonecutter_skips_unminable_nearest_stone_and_targets_next() -> None:
    now_ms = [0]
    world = World()
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    # Nearest stone from mine worker position, but fully blocked by occupied tiles.
    world._stones[(20, 20)] = Stone(units=10)  # noqa: SLF001
    for t in [(19, 19), (20, 19), (21, 19), (19, 20), (21, 20), (19, 21), (20, 21), (21, 21)]:
        world.mark_occupied(t[0], t[1], 1, 1)
    # Second stone is reachable and should be selected instead.
    world._stones[(24, 24)] = Stone(units=10)  # noqa: SLF001

    resources = ResourceManager()
    registry = BuildingRegistry(world)
    registry.place(TownHall, (16, 16)).level = 3
    mine = registry.place(StoneMine, (22, 22))
    workers = WorkerManager(resources, registry, now_ms_fn=lambda: now_ms[0])
    worker = workers.hire("STONECUTTER")
    assert worker is not None
    workers.reassign_all()

    now_ms[0] = 120_000
    workers.update(now_ms[0])
    assert worker.assigned_building is mine
    assert worker.state in {"going_to_stone", "mining", "returning", "arrived_camp", "depositing", "working"}
    assert worker.target_tree == (24, 24)
