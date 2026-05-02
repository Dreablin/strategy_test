"""Mill panel layout, click actions, and blocked hints."""

from __future__ import annotations

import pygame

from game.buildings.mill import Mill
from game.ui.mill_panel import MillPanel


def test_mill_panel_supports_building_and_toggle_click() -> None:
    surface = pygame.Surface((800, 600))
    mill = Mill(level=1, grid_pos=(10, 10))
    layout = MillPanel.layout(surface, mill, worker_assigned=False, production_status="No wheat")
    assert MillPanel.supports_building(mill) is True
    assert MillPanel.click_action(
        surface,
        layout.toggle.center,
        mill,
        worker_assigned=False,
        production_status="No wheat",
    ) == "toggle_active"


def test_mill_panel_blocked_reason_hints() -> None:
    mill = Mill(level=1, grid_pos=(10, 10))
    assert MillPanel.blocked_reason(mill, production_status="No worker") == "no worker"
    assert MillPanel.blocked_reason(mill, production_status="No wheat") == "no wheat"
    mill.set_active(False)
    assert MillPanel.blocked_reason(mill, production_status="Inactive") == "inactive"
    mill.set_active(True)
    mill.add_wheat_in(1)
    mill.add_flour_out(mill.output_capacity())
    assert MillPanel.blocked_reason(mill, production_status="Output full") == "output full"
    mill.take_flour_out(mill.output_capacity())
    assert MillPanel.blocked_reason(mill, production_status="Processing") == "running"
