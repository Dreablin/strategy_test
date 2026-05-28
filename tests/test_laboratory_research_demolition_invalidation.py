"""Laboratory demolition invalidates research deliveries (T426)."""

from __future__ import annotations

from game.buildings.laboratory import Laboratory
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.research_start import try_start_active_research
from game.research_state import ResearchState
from game.world import World
from game.workers import TransportTask, WorkerManager


def _setup() -> tuple[BuildingRegistry, TownHall, Laboratory, ResearchState]:
    world = World(world_seed=7)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    laboratory = registry.place(Laboratory, near_town_hall_tile(10, 10))
    laboratory.construction_site = None
    state = ResearchState()
    try_start_active_research("1", research_state=state, registry=registry)
    return registry, town_hall, laboratory, state


def _advance_until_idle_without_task(
    workers: WorkerManager,
    carrier,
    *,
    start_ms: int = 0,
    max_steps: int = 200,
    step_ms: int = 1_000,
) -> None:
    now_ms = start_ms
    for _ in range(max_steps):
        workers.update(now_ms)
        if carrier.transport_task is None and carrier.carrying is None and carrier.state == "idle":
            return
        now_ms += step_ms
    raise AssertionError("carrier did not finish cancelled delivery")


def test_queued_laboratory_research_tasks_removed_when_laboratory_demolished() -> None:
    registry, town_hall, laboratory, state = _setup()
    town_hall.add_to_warehouse("wood", 5)
    town_hall.add_to_warehouse("boards", 5)
    workers = WorkerManager(registry, now_ms_fn=lambda: 0, research_state=state)
    workers.update(0)
    assert any(t.purpose == "laboratory_research" for t in workers._transport_queue)  # noqa: SLF001

    registry.demolish(laboratory, workers)

    assert not any(t.purpose == "laboratory_research" for t in workers._transport_queue)  # noqa: SLF001
    assert not state.has_active_research()


def test_demolish_laboratory_cancels_active_research_state() -> None:
    registry, _, laboratory, state = _setup()
    workers = WorkerManager(registry, now_ms_fn=lambda: 0, research_state=state)
    assert state.has_active_research()

    registry.demolish(laboratory, workers)

    assert not state.has_active_research()
    assert state.active_research_id() is None


def test_carrier_returns_wood_to_town_hall_when_laboratory_demolished_mid_route() -> None:
    registry, town_hall, laboratory, state = _setup()
    workers = WorkerManager(registry, now_ms_fn=lambda: 0, research_state=state)
    carrier = workers.hire("CARRIER")
    assert carrier is not None
    carrier.current_tile = near_town_hall_tile(6, 8)
    carrier.stand_tile = carrier.current_tile
    carrier.state = "moving"
    carrier.transport_task = TransportTask(
        "wood",
        town_hall,
        laboratory,
        priority=10,
        purpose="laboratory_research",
    )
    carrier.carrying = "wood"

    registry.demolish(laboratory, workers)
    workers.update(0)

    assert carrier.transport_task is not None
    assert carrier.transport_task.returning_to_town_hall
    assert carrier.transport_task.target is town_hall

    _advance_until_idle_without_task(workers, carrier, start_ms=1_000)

    assert town_hall.warehouse_amount("wood") == 1
    assert laboratory not in registry.all()
    assert carrier.transport_task is None
    assert carrier.state == "idle"


def test_carrier_not_trapped_after_laboratory_demolished_before_pickup() -> None:
    registry, town_hall, laboratory, state = _setup()
    town_hall.add_to_warehouse("wood", 1)
    workers = WorkerManager(registry, now_ms_fn=lambda: 0, research_state=state)
    carrier = workers.hire("CARRIER")
    assert carrier is not None
    workers.enqueue_transport_task(
        resource="wood",
        source=town_hall,
        target=laboratory,
        amount=1,
        purpose="laboratory_research",
    )

    for now_ms in range(0, 30_000, 500):
        workers.update(now_ms)
        if carrier.transport_task is not None:
            break

    registry.demolish(laboratory, workers)

    _advance_until_idle_without_task(workers, carrier, start_ms=30_000)

    assert carrier.transport_task is None
    assert carrier.carrying is None
    assert carrier.state == "idle"
