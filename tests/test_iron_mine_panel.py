"""Iron Mine panel progress display."""

import pygame

from game.buildings.farm import Farm
from game.buildings.iron_mine import IronMine
from game.ui.iron_mine_panel import IronMinePanel


def test_iron_mine_panel_supports_only_iron_mine() -> None:
    assert IronMinePanel.supports_building(IronMine(level=1, grid_pos=(10, 10)))
    assert not IronMinePanel.supports_building(Farm(level=1, grid_pos=(10, 10)))


def test_iron_mine_panel_draws_progress_bar_for_active_mining() -> None:
    surface = pygame.Surface((900, 700), pygame.SRCALPHA)
    mine = IronMine(level=1, grid_pos=(10, 10))
    mine.mining_started_ms = 1_000
    mine.mining_duration_ms = 45_000
    layout = IronMinePanel.layout(surface, mine, worker_assigned=True, production_status="Mining")

    IronMinePanel.draw(
        surface,
        mine,
        worker_assigned=True,
        worker_status="assigned",
        production_status="mining",
        now_ms=23_500,
    )

    details_y = layout.frame.top + 16 + 4 * 26 + 32
    bar_y = details_y + 26
    sample_x = layout.frame.left + 24
    assert surface.get_at((sample_x, bar_y + 6))[:3] == (196, 116, 92)


def test_iron_mine_click_close_uses_extended_panel_bounds() -> None:
    surface = pygame.Surface((900, 700))
    mine = IronMine(level=1, grid_pos=(10, 10))
    layout = IronMinePanel.layout(surface, mine, worker_assigned=False)

    assert IronMinePanel.click_action(surface, layout.close.center, mine, worker_assigned=False) == "close"
