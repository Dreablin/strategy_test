"""Headless tests for construction-specific building panel UI (T201)."""

import pygame

from game.buildings.lumber_camp import LumberCamp
from game.construction import ConstructionSite
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
    assert ConstructionPanel.builder_status(camp) == "Waiting for resources"

    camp.construction_site = _site(delivered=2, required=2, started_ms=None)
    assert ConstructionPanel.builder_status(camp) == "Waiting for builder"

    camp.construction_site = _site(delivered=2, required=2, started_ms=0)
    assert ConstructionPanel.builder_status(camp) == "Building..."


def test_construction_panel_draw_smoke_with_progress_bar() -> None:
    surface = pygame.Surface((900, 700))
    camp = LumberCamp(level=1, grid_pos=(10, 10))
    camp.construction_site = _site(delivered=2, required=2, started_ms=0, target_level=2)

    ConstructionPanel.draw(surface, camp, now_ms=5_000)

    assert surface.get_at((450, 350)) != (0, 0, 0, 255)
