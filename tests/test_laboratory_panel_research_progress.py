"""Laboratory panel research point progress UI tests (T433)."""

from __future__ import annotations

import pygame

from game.research_config import RESEARCH_BY_ID
from game.research_start import try_start_active_research
from game.research_state import ResearchState
from game.ui.laboratory_panel import LaboratoryPanel
from game.ui.laboratory_panel_research import (
    research_points_fill_ratio,
    research_points_label,
    research_storage_section_height,
)
from tests.test_laboratory_panel import _built_laboratory


def test_research_points_label_and_ratio() -> None:
    state = ResearchState()
    state.start_research("1")
    state.add_delivered("wood", RESEARCH_BY_ID["1"].resource_cost["wood"])
    state.add_delivered("boards", RESEARCH_BY_ID["1"].resource_cost["boards"])
    state.add_points(350)
    assert research_points_label(state) == "350 / 5000"
    assert research_points_fill_ratio(state) == 350 / 5000


def test_section_height_includes_progress_block() -> None:
    laboratory, workers = _built_laboratory(level=1)
    state = ResearchState()
    registry = workers._registry  # noqa: SLF001
    try_start_active_research("1", research_state=state, registry=registry)
    without_progress = research_storage_section_height(laboratory, research_state=None)
    with_progress = research_storage_section_height(laboratory, research_state=state)
    assert with_progress > without_progress


def test_panel_draws_progress_bar_fill() -> None:
    laboratory, workers = _built_laboratory(level=1)
    state = ResearchState()
    registry = workers._registry  # noqa: SLF001
    try_start_active_research("1", research_state=state, registry=registry)
    for resource, amount in RESEARCH_BY_ID["1"].resource_cost.items():
        state.add_delivered(resource, amount)
    state.add_points(2500)
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
    research_h = research_storage_section_height(laboratory, research_state=state)
    section_top = layout.frame.bottom - 16 - research_h + 8
    bar_y = section_top + 48 + 8
    bar_x = layout.frame.left + 24
    fill_pixel = surface.get_at((bar_x + 40, bar_y + 6))
    assert fill_pixel[0] > 60
    assert research_points_label(state) == "2500 / 5000"
