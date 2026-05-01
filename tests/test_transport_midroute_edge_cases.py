"""RED tests for transport mid-route edge cases (T239)."""

from __future__ import annotations

from game.buildings.farm import Farm
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.world import World
from game.workers import WorkerManager


def _advance_until_loading(workers: WorkerManager, carrier, *, max_steps: int = 200, step_ms: int = 500) -> None:
    now_ms = 0
    for _ in range(max_steps):
        workers.update(now_ms)
        if carrier.state == "carrier_loading":
            return
        now_ms += step_ms
    raise AssertionError("carrier never reached loading state")


def test_stale_farm_wheat_task_is_dropped_when_source_empty_mid_route() -> None:
    world = World(world_seed=9)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    farm = registry.place(Farm, near_town_hall_tile(10, 8))
    farm.construction_site = None
    farm.stored = 1

    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    carrier = workers.hire("CARRIER")
    assert carrier is not None

    workers.enqueue_transport_task(resource="wheat", source=farm, target=town_hall, amount=1, priority=0)
    _advance_until_loading(workers, carrier)

    # Mid-route source mutation: wheat already removed elsewhere.
    farm.stored = 0
    carrier.camp_wait_until_ms = 0
    workers.update(5_000)

    # Expect stale task to be removed, not left to clog queue retries.
    assert carrier.transport_task is None
    assert carrier.state == "idle"
    assert not any(
        t.resource == "wheat" and t.source is farm and t.target is town_hall
        for t in workers._transport_queue  # noqa: SLF001
    )

