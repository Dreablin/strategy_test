"""Forester Hut panel layout and click-actions."""

import pygame

from game.buildings.forester_hut import ForesterHut
from game.ui.forester_hut_panel import ForesterHutPanel


def test_forester_hut_panel_buttons_do_not_overlap() -> None:
    surface = pygame.Surface((800, 600))
    resources = None
    hut = ForesterHut(level=1, grid_pos=(10, 10))
    layout = ForesterHutPanel.layout(surface, hut, resources, worker_assigned=False)
    assert layout.demolish is not None
    assert layout.demolish.bottom <= layout.toggle.top


def test_forester_hut_panel_click_actions_for_demolish_and_toggle() -> None:
    surface = pygame.Surface((800, 600))
    resources = None
    hut = ForesterHut(level=1, grid_pos=(10, 10))
    layout = ForesterHutPanel.layout(surface, hut, resources, worker_assigned=False)
    assert layout.demolish is not None
    assert (
        ForesterHutPanel.click_action(
            surface, layout.demolish.center, hut, resources, worker_assigned=False
        )
        == "demolish"
    )
    assert (
        ForesterHutPanel.click_action(surface, layout.toggle.center, hut, resources, worker_assigned=False)
        == "toggle_active"
    )
