"""Failing localized-assignment tests for worker dispatch (T141)."""

from __future__ import annotations

import game.workers as workers_mod
from game.buildings.lumber_camp import LumberCamp
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.world import World
from game.workers import Worker, WorkerManager, building_center_tile


def _manhattan(a: tuple[int, int], b: tuple[int, int]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def test_reassign_all_prefers_closest_target_and_bounded_path_calls(monkeypatch) -> None:
    world = World()
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    registry.place(TownHall, (26, 26))

    # Place far camps first to expose non-localized target ordering.
    far_positions = [
        (2, 2),
        (2, 18),
        (2, 40),
        (18, 2),
        (18, 40),
        (36, 2),
        (36, 40),
        (48, 2),
        (48, 18),
    ]
    camps = [registry.place(LumberCamp, pos) for pos in far_positions]
    closest = registry.place(LumberCamp, (12, 9))
    camps.append(closest)

    worker = Worker("LUMBERJACK", stand_tile=(10, 10))
    wm = WorkerManager(registry)
    wm.add_worker(worker)

    calls = {"n": 0}
    real = workers_mod.find_path_bfs

    def counted(*args, **kwargs):  # noqa: ANN002, ANN003
        calls["n"] += 1
        return real(*args, **kwargs)

    monkeypatch.setattr(workers_mod, "find_path_bfs", counted)
    wm.reassign_all()

    assert worker.assigned_building is closest
    nearest_dist = min(_manhattan(worker.current_tile, building_center_tile(camp)) for camp in camps)
    assert _manhattan(worker.current_tile, building_center_tile(worker.assigned_building)) == nearest_dist

    approach_count = len(wm._approach_tiles(closest))  # noqa: SLF001
    assert calls["n"] <= 2 * approach_count
