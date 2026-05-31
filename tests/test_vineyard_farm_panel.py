"""Vineyard Farm panel shell layout and click routing (T333)."""

from __future__ import annotations

import pygame

from game.buildings.vineyard_farm import VineyardFarm
from game.ui.vineyard_farm_panel import VineyardFarmPanel


def test_vineyard_farm_panel_supports_building_toggle_and_close_clicks() -> None:
    surface = pygame.Surface((1280, 720))
    farm = VineyardFarm(level=1, grid_pos=(10, 10))
    assert VineyardFarmPanel.supports_building(farm) is True
    assert VineyardFarmPanel.supports_building(object()) is False

    layout = VineyardFarmPanel.layout(surface, farm, worker_assigned=False, production_status="ready")
    assert layout.frame.contains(layout.toggle)
    assert VineyardFarmPanel.click_action(
        surface,
        layout.toggle.center,
        farm,
        worker_assigned=False,
        production_status="ready",
    ) == "toggle_active"
    assert (
        VineyardFarmPanel.click_action(
            surface,
            layout.close.center,
            farm,
            worker_assigned=False,
            production_status="ready",
        )
        == "close"
    )


def test_vineyard_farm_panel_draw_covers_toggle_region() -> None:
    surface = pygame.Surface((800, 600))
    farm = VineyardFarm(level=1, grid_pos=(10, 10))
    VineyardFarmPanel.draw(
        surface,
        farm,
        worker_assigned=True,
        worker_status="resting",
        production_status="resting",
        now_ms=0,
    )
    layout = VineyardFarmPanel.layout(surface, farm, worker_assigned=True, production_status="resting")
    px = surface.get_at((layout.toggle.centerx, layout.toggle.centery))
    assert px[0] > 30 or px[1] > 30 or px[2] > 30


def test_grape_storage_line_reflects_amounts() -> None:
    farm = VineyardFarm(level=2, grid_pos=(0, 0))
    farm.grapes_in = 2
    line = VineyardFarmPanel.grape_storage_line(farm)
    assert "2 /" in line
    assert str(farm.grapes_capacity()) in line


def test_max_level_panel_grape_row_clear_of_demolish_and_toggle() -> None:
    surface = pygame.Surface((1280, 720))
    farm = VineyardFarm(level=10, grid_pos=(0, 0))
    farm.construction_site = None
    layout = VineyardFarmPanel.layout(surface, farm, worker_assigned=True, production_status="ready")
    assert layout.upgrade is None
    assert layout.demolish is not None
    grape_y = VineyardFarmPanel._grape_label_y(layout)
    row = 26
    assert grape_y + row <= layout.demolish.top
    assert layout.toggle.top >= layout.demolish.bottom


def test_draw_leaves_grape_text_above_demolish_at_level_10() -> None:
    surface = pygame.Surface((1280, 720))
    farm = VineyardFarm(level=10, grid_pos=(0, 0))
    farm.construction_site = None
    farm.grapes_in = 7
    VineyardFarmPanel.draw(
        surface,
        farm,
        worker_assigned=True,
        worker_status="resting",
        production_status="resting",
        now_ms=0,
    )
    layout = VineyardFarmPanel.layout(surface, farm, worker_assigned=True, production_status="resting")
    grape_y = VineyardFarmPanel._grape_label_y(layout)
    panel_bg = (36, 40, 52, 255)
    text_found = False
    for x in range(layout.frame.left + 16, layout.frame.right - 16):
        px = surface.get_at((x, grape_y + 10))
        if px != panel_bg:
            text_found = True
            break
    assert text_found
