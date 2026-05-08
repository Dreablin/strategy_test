"""Well panel progress display."""

import pygame

from game.buildings.well import Well
from game.ui.well_panel import WellPanel


def test_well_panel_draws_storage_progress_and_toggle() -> None:
    surface = pygame.Surface((800, 600))
    well = Well(level=1, grid_pos=(10, 10))
    well.processing_started_ms = 5_000
    well.processing_duration_ms = 10_000

    WellPanel.draw(
        surface,
        well,
        worker_assigned=True,
        worker_status="assigned",
        production_status="Processing",
        now_ms=10_000,
    )

    layout = WellPanel.layout(surface, well, worker_assigned=True, production_status="Processing")
    assert surface.get_at((layout.frame.left + 40, layout.frame.top + 150)) != (0, 0, 0, 255)
