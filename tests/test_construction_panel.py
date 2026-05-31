"""Headless tests for construction-specific building panel UI (T201)."""

import pygame

from game import i18n
from game.buildings.lumber_camp import LumberCamp
from game.construction import ConstructionSite
from game.ui.building_panel import building_display_name
from game.ui.construction_panel import ConstructionPanel


def _site(*, delivered: int, required: int, started_ms: int | None = None, target_level: int = 1) -> ConstructionSite:
    return ConstructionSite(
        required_resources={"wood": required},
        delivered_resources={"wood": delivered},
        build_time_ms=10_000,
        build_started_ms=started_ms,
        builder=None,
        target_level=target_level,
    )


def test_construction_panel_close_click_action() -> None:
    surface = pygame.Surface((800, 600))
    camp = LumberCamp(level=1, grid_pos=(10, 10))
    camp.construction_site = _site(delivered=0, required=2)
    layout = ConstructionPanel.layout(surface, camp)

    assert ConstructionPanel.click_action(surface, layout.close.center, camp) == "close"
    assert ConstructionPanel.click_action(surface, layout.demolish.center, camp) == "demolish"
    assert ConstructionPanel.click_action(surface, layout.frame.center, camp) is None


def test_construction_panel_builder_status_text_states() -> None:
    camp = LumberCamp(level=1, grid_pos=(10, 10))

    camp.construction_site = _site(delivered=0, required=2)
    assert ConstructionPanel.builder_status(camp) == i18n.t("status.construction.waiting_resources")

    camp.construction_site = _site(delivered=2, required=2, started_ms=None)
    assert ConstructionPanel.builder_status(camp) == i18n.t("status.construction.waiting_builder")

    camp.construction_site = _site(delivered=2, required=2, started_ms=0)
    assert ConstructionPanel.builder_status(camp) == i18n.t("status.construction.building")


def test_construction_panel_upgrading_title() -> None:
    camp = LumberCamp(level=1, grid_pos=(10, 10))
    camp.construction_site = _site(delivered=0, required=2, target_level=2)
    assert ConstructionPanel.title_line(camp) == i18n.t("ui.construction.upgrading_to", level=2)


def test_construction_panel_resource_delivery_line() -> None:
    assert ConstructionPanel.resource_delivery_line("wood", 1, 3) == i18n.t(
        "ui.construction.delivered",
        label=i18n.t("resource.wood"),
        delivered=1,
        required=3,
    )


def test_construction_panel_localized_name_ru(use_locale) -> None:
    with use_locale("ru"):
        assert building_display_name("LUMBER_CAMP") == "Лагерь лесорубов"
        camp = LumberCamp(level=1, grid_pos=(0, 0))
        camp.construction_site = _site(delivered=0, required=1)
        assert ConstructionPanel.builder_status(camp) == i18n.t("status.construction.waiting_resources")


def test_construction_panel_draw_smoke_with_progress_bar() -> None:
    surface = pygame.Surface((900, 700))
    camp = LumberCamp(level=1, grid_pos=(10, 10))
    camp.construction_site = _site(delivered=2, required=2, started_ms=0, target_level=2)

    ConstructionPanel.draw(surface, camp, now_ms=5_000)

    assert surface.get_at((450, 350)) != (0, 0, 0, 255)
