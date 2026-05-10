"""Cow farm panel shell: layout and active toggle (T300)."""

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
    layout = CowFarmPanel.layout(surface, farm, worker_assigned=False, production_status=None)
    sy = CowFarmPanel.storage_block_top(layout.frame.top)
    storage_bottom_approx = sy + 4 * 22 + 20
    assert layout.upgrade is not None and layout.demolish is not None
    assert storage_bottom_approx < layout.upgrade.top - 4


def test_cow_farm_panel_storage_block_clears_demolish_at_max_level() -> None:
    surface = pygame.Surface((1280, 720))
    farm = CowFarm(level=CowFarm.max_level(), grid_pos=(10, 10))
    layout = CowFarmPanel.layout(surface, farm, worker_assigned=False, production_status=None)
    sy = CowFarmPanel.storage_block_top(layout.frame.top)
    storage_bottom_approx = sy + 4 * 22 + 20
    assert layout.upgrade is None and layout.demolish is not None
    assert storage_bottom_approx < layout.demolish.top - 4
