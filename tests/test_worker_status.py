"""Tests for worker/production status ids and localization (T454)."""

from __future__ import annotations

from game import i18n
from game.buildings.lumber_camp import LumberCamp
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.worker_models import Worker
from game.worker_status import localized_status, production_status_for_building, worker_status_for_building
from game.workers import WorkerManager
from game.world import World


def _registry() -> tuple[BuildingRegistry, WorkerManager]:
    world = World(world_seed=5)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    workers = WorkerManager(registry, now_ms_fn=lambda: 0)
    return registry, workers


def test_production_status_returns_stable_ids() -> None:
    registry, workers = _registry()
    camp = registry.place(LumberCamp, near_town_hall_tile(10, 10))
    camp.construction_site = None
    assert production_status_for_building(workers, camp) == "no_worker"


def test_worker_status_returns_stable_ids() -> None:
    registry, workers = _registry()
    camp = registry.place(LumberCamp, near_town_hall_tile(10, 10))
    camp.construction_site = None
    cx, cy = camp.grid_pos  # type: ignore[misc]
    worker = Worker("LUMBERJACK", stand_tile=(cx - 4, cy))
    workers.add_worker(worker)
    workers.reassign_all()
    assert worker_status_for_building(workers, camp) == "on_the_way"


def test_localized_status_en_representative_samples() -> None:
    assert localized_status("no_worker") == i18n.t("status.no_worker")
    assert localized_status("output_full") == i18n.t("status.output_full")
    assert localized_status("on_the_way") == i18n.t("status.on_the_way")
    assert localized_status("sowing") == i18n.t("status.sowing")


def test_localized_status_ru_smoke(use_locale) -> None:
    with use_locale("ru"):
        assert localized_status("no_worker") == i18n.t("status.no_worker")
        assert localized_status("ready") == i18n.t("status.ready")
        assert i18n.t("status.processing") == i18n.t("status.processing")
