"""RED tests for farmer assignment lifecycle (T230)."""

from __future__ import annotations

from game.buildings.farm import Farm
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.world import World
from game.workers import WorkerManager


def _advance(workers: WorkerManager, now_ms: dict[str, int], *, steps: int = 800, step_ms: int = 500) -> None:
    for _ in range(steps):
        now_ms["t"] += step_ms
        workers.reassign_all()
        workers.update(now_ms["t"])


def test_farmer_gets_assigned_to_built_farm_and_enters_rest_state() -> None:
    now_ms = {"t": 0}
    world = World(world_seed=0)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    farm = registry.place(Farm, near_town_hall_tile(10, 8))
    farm.construction_site = None

    workers = WorkerManager(registry, now_ms_fn=lambda: now_ms["t"])
    farmer = workers.hire("FARMER")
    assert farmer is not None

    _advance(workers, now_ms, steps=1200)

    assert farmer.assigned_building is farm
    assert farmer.state == "resting"


def test_farmer_starts_field_work_cycle_from_farm_home_base_after_rest() -> None:
    now_ms = {"t": 0}
    world = World(world_seed=0)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    farm = registry.place(Farm, near_town_hall_tile(10, 8))
    farm.construction_site = None

    workers = WorkerManager(registry, now_ms_fn=lambda: now_ms["t"])
    farmer = workers.hire("FARMER")
    assert farmer is not None

    _advance(workers, now_ms, steps=2000)

    assert farmer.assigned_building is farm
    assert farmer.current_tile == (farm.grid_pos[0] + 1, farm.grid_pos[1] + 1)
    assert farmer.state in {"moving", "going_to_field", "working_field", "sowing", "harvesting"}
