"""FARMER may staff VINEYARD_FARM as well as FARM (T328)."""

from __future__ import annotations

from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.buildings.vineyard_farm import VineyardFarm
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.world import World
from game.workers import WorkerManager


def test_reassign_all_assigns_idle_farmer_to_only_vineyard_farm() -> None:
    now_ms = {"t": 0}
    world = World(world_seed=0)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    vf = registry.place(VineyardFarm, near_town_hall_tile(12, 8))
    vf.construction_site = None

    workers = WorkerManager(registry, now_ms_fn=lambda: now_ms["t"])
    farmer = workers.hire("FARMER")
    assert farmer is not None
    for _ in range(400):
        now_ms["t"] += 500
        workers.reassign_all()
        workers.update(now_ms["t"])
        if farmer.assigned_building is vf:
            break
    assert farmer.assigned_building is vf
