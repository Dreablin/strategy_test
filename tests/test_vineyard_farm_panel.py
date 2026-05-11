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

    layout = VineyardFarmPanel.layout(surface, farm, worker_assigned=False, production_status="Ready")
    assert layout.frame.contains(layout.toggle)
    assert VineyardFarmPanel.click_action(
        surface,
        layout.toggle.center,
        farm,
        worker_assigned=False,
        production_status="Ready",
    ) == "toggle_active"
    assert (
        VineyardFarmPanel.click_action(
            surface,
            layout.close.center,
            farm,
            worker_assigned=False,
            production_status="Ready",
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
        production_status="Resting",
        now_ms=0,
    )
    layout = VineyardFarmPanel.layout(surface, farm, worker_assigned=True, production_status="Resting")
    px = surface.get_at((layout.toggle.centerx, layout.toggle.centery))
    assert px[0] > 30 or px[1] > 30 or px[2] > 30
