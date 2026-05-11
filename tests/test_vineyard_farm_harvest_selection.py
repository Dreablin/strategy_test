"""Vineyard Farm ripe-plot selection and reservation (T327)."""

from __future__ import annotations

from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.buildings.vineyard import Vineyard
from game.buildings.vineyard_farm import VineyardFarm
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.worker_geometry import select_ripe_vineyard_target_tile
from game.worker_models import Worker
from game.world import World
from game.workers import WorkerManager


def test_select_ripe_vineyard_target_prefers_tightest_chebyshev() -> None:
    home = (10, 10)
    ripe = [(12, 10), (11, 10)]
    assert select_ripe_vineyard_target_tile(
        farm_home=home,
        ripe_tiles=ripe,
        excluded_tiles=(),
        max_radius=5,
    ) == (11, 10)


def test_select_ripe_vineyard_target_returns_none_when_all_excluded() -> None:
    home = (10, 10)
    ripe = [(11, 10)]
    assert (
        select_ripe_vineyard_target_tile(
            farm_home=home,
            ripe_tiles=ripe,
            excluded_tiles={(11, 10)},
            max_radius=5,
        )
        is None
    )


def test_select_ripe_vineyard_respects_radius() -> None:
    home = (10, 10)
    ripe = [(20, 10)]
    assert (
        select_ripe_vineyard_target_tile(
            farm_home=home,
            ripe_tiles=ripe,
            excluded_tiles=(),
            max_radius=5,
        )
        is None
    )


def test_worker_manager_select_skips_plot_reserved_by_other_farmer() -> None:
    world = World()
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    farm = registry.place(VineyardFarm, near_town_hall_tile(16, 8))
    farm.construction_site = None
    a = registry.place(Vineyard, near_town_hall_tile(18, 8))
    b = registry.place(Vineyard, near_town_hall_tile(14, 8))
    a.construction_site = None
    b.construction_site = None
    a.set_growth_stage(4, now_ms=0)
    b.set_growth_stage(4, now_ms=0)
    w1 = Worker("FARMER", stand_tile=near_town_hall_tile(4, 4))
    w2 = Worker("FARMER", stand_tile=near_town_hall_tile(5, 4))
    wm = WorkerManager(registry, now_ms_fn=lambda: 0)
    wm.add_worker(w1)
    wm.add_worker(w2)
    assert wm._reserve_vineyard_plot(a, w1)  # noqa: SLF001
    picked = wm.select_ripe_vineyard_for_vineyard_farm(farm, claimer=w2)
    assert picked is b


def test_worker_manager_claimer_none_treats_all_reservations_as_blocked() -> None:
    world = World()
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    farm = registry.place(VineyardFarm, near_town_hall_tile(16, 8))
    farm.construction_site = None
    plot = registry.place(Vineyard, near_town_hall_tile(18, 8))
    plot.construction_site = None
    plot.set_growth_stage(4, now_ms=0)
    w1 = Worker("FARMER", stand_tile=near_town_hall_tile(4, 4))
    wm = WorkerManager(registry, now_ms_fn=lambda: 0)
    wm.add_worker(w1)
    wm._reserve_vineyard_plot(plot, w1)  # noqa: SLF001
    assert wm.select_ripe_vineyard_for_vineyard_farm(farm, claimer=None) is None


def test_notify_demolished_vineyard_clears_tile_reservation() -> None:
    world = World()
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    plot = registry.place(Vineyard, near_town_hall_tile(12, 12))
    plot.construction_site = None
    w = Worker("FARMER", stand_tile=near_town_hall_tile(4, 4))
    wm = WorkerManager(registry, now_ms_fn=lambda: 0)
    wm.add_worker(w)
    assert wm._reserve_vineyard_plot(plot, w)  # noqa: SLF001
    registry.demolish(plot, worker_manager=wm)
    assert not wm._vineyard_plot_reservations  # noqa: SLF001
