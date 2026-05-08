"""Canteen panel: layout, storage lines, toggle, upgrade/demolish, blocked hints."""

from __future__ import annotations

import pygame

from game.buildings.canteen import Canteen
from game.ui.canteen_panel import CanteenPanel


def test_canteen_panel_supports_building_and_toggle_click() -> None:
    surface = pygame.Surface((1280, 720))
    canteen = Canteen(level=1, grid_pos=(10, 10))
    layout = CanteenPanel.layout(surface, canteen, worker_assigned=False, production_status="No worker")
    assert CanteenPanel.supports_building(canteen) is True
    assert layout.upgrade is not None
    assert layout.demolish is not None
    assert (
        CanteenPanel.click_action(
            surface,
            layout.toggle.center,
            canteen,
            worker_assigned=False,
            production_status="No worker",
        )
        == "toggle_active"
    )


def test_canteen_panel_upgrade_and_demolish_click() -> None:
    surface = pygame.Surface((1280, 720))
    canteen = Canteen(level=1, grid_pos=(10, 10))
    layout = CanteenPanel.layout(surface, canteen, worker_assigned=False, production_status="No worker")
    assert CanteenPanel.click_action(surface, layout.upgrade.center, canteen, worker_assigned=False, production_status="No worker") == "upgrade"
    assert CanteenPanel.click_action(surface, layout.demolish.center, canteen, worker_assigned=False, production_status="No worker") == "demolish"


def test_canteen_panel_blocked_reason_hints() -> None:
    canteen = Canteen(level=1, grid_pos=(10, 10))
    assert (
        CanteenPanel.blocked_reason(canteen, worker_status="empty", production_status="No worker") == "no worker"
    )
    canteen.set_active(False)
    assert CanteenPanel.blocked_reason(canteen, worker_status="assigned", production_status="Inactive") == "inactive"
    canteen.set_active(True)
    canteen.add_local_storage("chicken", 1)
    canteen.add_local_storage("bread", 1)
    canteen.add_local_storage("water", 1)
    canteen.add_local_storage("simple_meal", canteen.local_storage_capacity("simple_meal"))
    assert (
        CanteenPanel.blocked_reason(canteen, worker_status="assigned", production_status="Output full")
        == "output full"
    )
    canteen.take_local_storage("simple_meal", canteen.local_storage_capacity("simple_meal"))
    assert CanteenPanel.blocked_reason(canteen, worker_status="assigned", production_status="Resting") == "resting"
    assert CanteenPanel.blocked_reason(canteen, worker_status="assigned", production_status="Processing") == "running"


def test_canteen_panel_draw_smoke_and_progress_bar() -> None:
    surface = pygame.Surface((1280, 720))
    canteen = Canteen(level=1, grid_pos=(10, 10))
    canteen.processing_started_ms = 1_000
    canteen.processing_duration_ms = 30_000
    mid = 15_000
    assert canteen.processing_progress(mid) > 0.4
    CanteenPanel.draw(
        surface,
        canteen,
        worker_assigned=True,
        worker_status="assigned",
        production_status="Processing",
        now_ms=mid,
    )
    layout = CanteenPanel.layout(surface, canteen, worker_assigned=True, production_status="Processing")
    bar_center_x = layout.frame.left + layout.frame.width // 2
    bar_sample_y = layout.frame.bottom - 80
    c = surface.get_at((bar_center_x, bar_sample_y))
    assert c.r > 80 or c.g > 80 or c.b > 80
