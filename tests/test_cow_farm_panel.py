"""Cow farm panel: layout, storage, blocked hint, progress bar, toggle."""

from __future__ import annotations

import pygame

from game.buildings.cow_farm import CowFarm
from game.ui.cow_farm_panel import CowFarmPanel


def test_cow_farm_panel_supports_building_and_toggle_click() -> None:
    surface = pygame.Surface((1280, 720))
    farm = CowFarm(level=1, grid_pos=(10, 10))
    layout = CowFarmPanel.layout(surface, farm, worker_assigned=False, production_status=None)
    assert CowFarmPanel.supports_building(farm) is True
    assert CowFarmPanel.click_action(
        surface,
        layout.toggle.center,
        farm,
        worker_assigned=False,
        production_status=None,
    ) == "toggle_active"


def test_cow_farm_panel_draw_smoke() -> None:
    surface = pygame.Surface((1280, 720))
    farm = CowFarm(level=1, grid_pos=(10, 10))
    CowFarmPanel.draw(
        surface,
        farm,
        worker_assigned=False,
        worker_status="empty",
        production_status=None,
        now_ms=0,
    )
    assert surface.get_at((640, 360)) != (0, 0, 0, 255)


def test_cow_farm_panel_storage_line_texts() -> None:
    farm = CowFarm(level=2, grid_pos=(10, 10))
    farm.add_wheat_in(2)
    farm.add_water_in(1)
    farm.add_beef_out(1)
    farm.add_hide_out(0)
    w, wat, beef, hide = CowFarmPanel.storage_line_texts(farm)
    cap = farm.wheat_capacity()
    assert w == f"Input wheat: 2 / {cap}"
    assert wat == f"Input water: 1 / {cap}"
    assert beef == f"Output beef: 1 / {cap}"
    assert hide == f"Output hide: 0 / {cap}"


def test_cow_farm_panel_storage_block_clears_upgrade_and_demolish() -> None:
    surface = pygame.Surface((1280, 720))
    farm = CowFarm(level=1, grid_pos=(10, 10))
    layout = CowFarmPanel.layout(surface, farm, worker_assigned=False, production_status="no_worker")
    sy = CowFarmPanel.storage_block_top(layout.frame.top)
    # Four storage lines, blocked line, progress bar (see cow_farm_panel layout constants).
    detail_bottom_approx = sy + 4 * 22 + 22 + 24 + 12 + 4
    assert layout.upgrade is not None and layout.demolish is not None
    assert detail_bottom_approx < layout.upgrade.top - 4


def test_cow_farm_panel_storage_block_clears_demolish_at_max_level() -> None:
    surface = pygame.Surface((1280, 720))
    farm = CowFarm(level=CowFarm.max_level(), grid_pos=(10, 10))
    layout = CowFarmPanel.layout(surface, farm, worker_assigned=False, production_status="no_worker")
    sy = CowFarmPanel.storage_block_top(layout.frame.top)
    detail_bottom_approx = sy + 4 * 22 + 22 + 24 + 12 + 4
    assert layout.upgrade is None and layout.demolish is not None
    assert detail_bottom_approx < layout.demolish.top - 4


def test_cow_farm_panel_blocked_reason_hints() -> None:
    farm = CowFarm(level=1, grid_pos=(10, 10))
    assert CowFarmPanel.blocked_reason(farm, worker_status="empty", production_status="no_worker") == "no worker"
    farm.set_active(False)
    assert CowFarmPanel.blocked_reason(farm, worker_status="assigned", production_status="inactive") == "inactive"
    farm.set_active(True)
    farm.add_wheat_in(3)
    farm.add_water_in(3)
    farm.add_beef_out(farm.beef_capacity())
    assert CowFarmPanel.blocked_reason(farm, worker_status="assigned", production_status="output_full") == "output full"
    farm.take_beef_out(farm.beef_capacity())
    assert CowFarmPanel.blocked_reason(farm, worker_status="assigned", production_status="processing") == "running"
    farm.take_wheat_in(3)
    assert CowFarmPanel.blocked_reason(farm, worker_status="assigned", production_status="ready") == "no wheat"
    farm.add_wheat_in(3)
    farm.take_water_in(3)
    assert CowFarmPanel.blocked_reason(farm, worker_status="assigned", production_status="ready") == "no water"
    farm.add_water_in(3)
    assert CowFarmPanel.blocked_reason(farm, worker_status="assigned", production_status="resting") == "resting"


def test_cow_farm_panel_progress_bar_shows_mid_cycle_fill() -> None:
    surface = pygame.Surface((1280, 720))
    farm = CowFarm(level=1, grid_pos=(10, 10))
    farm.processing_started_ms = 1000
    now_ms = 1000 + farm.processing_duration_ms // 2
    CowFarmPanel.draw(
        surface,
        farm,
        worker_assigned=True,
        worker_status="assigned",
        production_status="processing",
        now_ms=now_ms,
    )
    layout = CowFarmPanel.layout(surface, farm, worker_assigned=True, production_status="processing")
    sy = CowFarmPanel.storage_block_top(layout.frame.top)
    bar_y = sy + 4 * 22 + 24
    sample_x = layout.frame.left + 16 + 80
    sample_y = bar_y + 6
    px = surface.get_at((sample_x, sample_y))
    assert px[:3] == (214, 198, 154)
