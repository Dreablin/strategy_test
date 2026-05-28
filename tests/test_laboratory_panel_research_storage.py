"""Laboratory panel active research and input storage display tests (T423)."""

from __future__ import annotations

import pygame

from game.buildings.registry import BuildingRegistry
from game.research_config import RESEARCH_BY_ID
from game.research_start import try_start_active_research
from game.research_state import ResearchState
from game.ui.laboratory_panel import LaboratoryPanel
from game.ui.laboratory_panel_research import research_input_line, research_storage_section_height
from tests.test_laboratory_panel import _built_laboratory


def _registry_for(laboratory: object, workers: object) -> BuildingRegistry:
    return workers._registry  # noqa: SLF001


def test_no_research_section_without_active_research() -> None:
    laboratory, workers = _built_laboratory(level=1)
    assert research_storage_section_height(laboratory) == 0
    surface = pygame.Surface((1280, 720))
    LaboratoryPanel.draw(
        surface,
        laboratory,
        worker_assigned=False,
        production_status="No worker",
        worker_manager=workers,
        research_state=ResearchState(),
    )


def test_research_section_height_matches_resource_count() -> None:
    laboratory, workers = _built_laboratory(level=1)
    definition = RESEARCH_BY_ID["1"]
    laboratory.initialize_research_input_storage(definition.resource_cost)
    assert research_storage_section_height(laboratory) > 0
    assert len(laboratory.research_input_resources()) == len(definition.resource_cost)


def test_panel_draws_input_rows_with_delivered_amounts() -> None:
    laboratory, workers = _built_laboratory(level=1)
    state = ResearchState()
    registry = _registry_for(laboratory, workers)
    try_start_active_research("1", research_state=state, registry=registry)
    laboratory._research_input_delivered["wood"] = 5  # noqa: SLF001
    assert research_input_line(laboratory, "wood") == "Wood: 5 / 20"
    assert research_input_line(laboratory, "boards") == "Boards: 0 / 10"
    surface = pygame.Surface((1280, 720))
    surface.fill((28, 32, 40))
    layout = LaboratoryPanel.draw(
        surface,
        laboratory,
        worker_assigned=False,
        production_status="No worker",
        worker_manager=workers,
        research_state=state,
    )
    assert layout.research_section is not None
    section_top = layout.research_section.top
    pixel = surface.get_at((layout.frame.left + 20, section_top + 20))
    assert sum(pixel[:3]) > 40


def test_research_and_scientist_content_stays_above_action_buttons() -> None:
    laboratory, workers = _built_laboratory(level=1)
    state = ResearchState()
    registry = _registry_for(laboratory, workers)
    try_start_active_research("1", research_state=state, registry=registry)
    surface = pygame.Surface((1280, 720))

    layout = LaboratoryPanel.layout(
        surface,
        laboratory,
        worker_assigned=False,
        production_status="No worker",
        worker_manager=workers,
        research_state=state,
    )

    action_tops = [
        rect.top for rect in (layout.upgrade, layout.demolish) if rect is not None
    ]
    assert action_tops
    first_action_top = min(action_tops)
    assert layout.research_section is not None
    assert layout.research_section.bottom < first_action_top
    assert layout.scientist_tiles
    assert max(tile.bottom for tile in layout.scientist_tiles) < first_action_top
