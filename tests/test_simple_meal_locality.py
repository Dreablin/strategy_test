"""RED tests for simple_meal local-only behavior (T248)."""

from __future__ import annotations

import pytest

from game.buildings.canteen import Canteen
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.ui import town_hall_panel
from game.workers import WorkerManager
from game.world import World


def test_town_hall_rejects_simple_meal_in_warehouse() -> None:
    town_hall = TownHall(level=1, grid_pos=(10, 10))

    with pytest.raises(ValueError):
        town_hall.add_to_warehouse("simple_meal", 1)


def test_town_hall_storage_rows_do_not_show_simple_meal() -> None:
    keys = [key for key, _label in town_hall_panel._STORAGE_ROWS]  # noqa: SLF001
    assert "simple_meal" not in keys


def test_worker_manager_never_enqueues_simple_meal_export_from_canteen() -> None:
    world = World(world_seed=11)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    world._iron.clear()  # noqa: SLF001
    world._gold.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    canteen = registry.place(Canteen, near_town_hall_tile(12, 8))
    canteen.construction_site = None
    canteen.add_local_storage("simple_meal", 2)
    workers = WorkerManager(registry, now_ms_fn=lambda: 0)

    workers.update(0)

    assert not any(
        task.resource == "simple_meal"
        for task in workers._transport_queue  # noqa: SLF001
    )
