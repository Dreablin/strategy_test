"""Sawmill panel layout, click actions, and blocked hints."""

import pygame

from game.buildings.sawmill import Sawmill
from game.ui.sawmill_panel import SawmillPanel


def test_sawmill_panel_supports_building_and_toggle_click() -> None:
    surface = pygame.Surface((1280, 720))
    sawmill = Sawmill(level=1, grid_pos=(10, 10))
    layout = SawmillPanel.layout(surface, sawmill, worker_assigned=False, production_status="no_worker")
    assert SawmillPanel.supports_building(sawmill) is True
    assert SawmillPanel.click_action(
        surface,
        layout.toggle.center,
        sawmill,
        worker_assigned=False,
        production_status="no_worker",
    ) == "toggle_active"


def test_sawmill_panel_blocked_reason_hints() -> None:
    sawmill = Sawmill(level=1, grid_pos=(10, 10))
    assert SawmillPanel.blocked_reason(sawmill, worker_status="empty", production_status="no_worker") == "no worker"
    sawmill.set_active(False)
    assert SawmillPanel.blocked_reason(sawmill, worker_status="assigned", production_status="inactive") == "inactive"
    sawmill.set_active(True)
    sawmill.add_wood_in(1)
    sawmill.add_boards_out(sawmill.output_capacity())
    assert SawmillPanel.blocked_reason(sawmill, worker_status="assigned", production_status="output_full") == "output full"
