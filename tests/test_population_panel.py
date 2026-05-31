"""Population panel worker summary and localization tests."""

from __future__ import annotations

import pygame

from game import i18n
from game.buildings.farm import Farm
from game.buildings.lumber_camp import LumberCamp
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.ui.building_panel import building_display_name
from game.ui.population_panel import PopulationPanel, worker_summary
from game.ui.worker_labels import worker_display_label
from game.worker_models import TransportTask, Worker
from game.world import World


def test_worker_summary_idle_assigned_farmer() -> None:
    world = World(world_seed=3)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    farm = registry.place(Farm, near_town_hall_tile(12, 8))
    farm.construction_site = None

    worker = Worker("FARMER", stand_tile=near_town_hall_tile())
    worker.state = "sowing"
    worker.assigned_building = farm

    title, task_line, detail = worker_summary(worker)
    assert title == worker_display_label("FARMER")
    assert task_line == i18n.t("status.worker.sowing")
    assert detail == i18n.t("ui.worker.assigned", building=building_display_name("FARM"))


def test_worker_summary_transport_task() -> None:
    world = World(world_seed=4)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    th = registry.place(TownHall, town_hall_origin_tile())
    camp = registry.place(LumberCamp, near_town_hall_tile(14, 8))
    camp.construction_site = None

    worker = Worker("CARRIER", stand_tile=near_town_hall_tile())
    worker.transport_task = TransportTask(resource="wood", source=camp, target=th, purpose="generic")
    worker.carrying = "wood"

    _, task_line, detail = worker_summary(worker)
    assert task_line == i18n.t(
        "ui.population.transport_task",
        action=i18n.t("ui.population.action.carrying"),
        resource=i18n.t("resource.wood"),
    )
    assert detail == i18n.t(
        "ui.population.route",
        source=building_display_name("LUMBER_CAMP"),
        target=building_display_name("TOWN_HALL"),
    )


def test_worker_summary_assigned_with_carrying() -> None:
    worker = Worker("CARRIER", stand_tile=near_town_hall_tile())
    worker.state = "moving"
    worker.carrying = "boards"

    _, _, detail = worker_summary(worker)
    assert detail == i18n.t(
        "ui.population.assigned_carrying",
        building=i18n.t("ui.common.none"),
        resource=i18n.t("resource.boards"),
    )


def test_population_panel_layout_and_filter_click() -> None:
    surface = pygame.Surface((1280, 720))
    workers = (
        Worker("CARRIER", stand_tile=near_town_hall_tile()),
        Worker("BUILDER", stand_tile=near_town_hall_tile()),
    )
    layout = PopulationPanel.layout(surface, workers)
    assert PopulationPanel.click_action(surface, layout.close.center, workers) == "close"
    assert PopulationPanel.click_action(surface, layout.filters[0][1].center, workers) == "filter:all"


def test_population_panel_worker_at_respects_scroll() -> None:
    surface = pygame.Surface((1280, 720))
    workers = tuple(Worker("CARRIER", stand_tile=near_town_hall_tile()) for _ in range(12))
    layout = PopulationPanel.layout(surface, workers, scroll_y=0)
    hit = PopulationPanel.worker_at(surface, (layout.content.centerx, layout.content.top + 10), workers, scroll_y=0)
    assert hit is workers[0]


def test_population_panel_ru_smoke(use_locale) -> None:
    with use_locale("ru"):
        worker = Worker("FARMER", stand_tile=near_town_hall_tile())
        worker.state = "idle"
        _, task_line, _ = worker_summary(worker)
        assert task_line == i18n.t("status.worker.idle")
        assert i18n.t("ui.population.title", count=1) != "ui.population.title"
