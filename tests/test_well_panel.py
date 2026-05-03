"""Well panel progress display."""

import pygame

from game.buildings.well import Well
from game.ui.well_panel import WellPanel


def test_well_panel_draws_progress_bar_for_active_water_draw() -> None:
    surface = pygame.Surface((800, 600))
    well = Well(level=1, grid_pos=(10, 10))

    WellPanel.draw(
        surface,
        well,
        worker_assigned=True,
        worker_status="drawing water",
        production_status="Drawing water",
        draw_progress=0.5,
    )

    assert surface.get_at((400, 300)) != (0, 0, 0, 255)
