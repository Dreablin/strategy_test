"""Chicken farm panel layout, click actions, and blocked hints."""

from __future__ import annotations

import pygame

from game.buildings.chicken_farm import ChickenFarm
from game.ui.chicken_farm_panel import ChickenFarmPanel


def test_chicken_farm_panel_supports_building_and_toggle_click() -> None:
    surface = pygame.Surface((1280, 720))
    farm = ChickenFarm(level=1, grid_pos=(10, 10))
    layout = ChickenFarmPanel.layout(surface, farm, worker_assigned=False, production_status="no_worker")
    assert ChickenFarmPanel.supports_building(farm) is True
    assert ChickenFarmPanel.click_action(
        surface,
        layout.toggle.center,
        farm,
        worker_assigned=False,
        production_status="no_worker",
    ) == "toggle_active"


def test_chicken_farm_panel_blocked_reason_hints() -> None:
    farm = ChickenFarm(level=1, grid_pos=(10, 10))
    assert ChickenFarmPanel.blocked_reason(farm, worker_status="empty", production_status="no_worker") == "no worker"
    farm.set_active(False)
    assert ChickenFarmPanel.blocked_reason(farm, worker_status="assigned", production_status="inactive") == "inactive"
    farm.set_active(True)
    farm.add_wheat_in(1)
    farm.add_water_in(1)
    farm.add_chicken_out(farm.output_capacity())
    assert ChickenFarmPanel.blocked_reason(farm, worker_status="assigned", production_status="output_full") == "output full"
    farm.take_chicken_out(farm.output_capacity())
    assert ChickenFarmPanel.blocked_reason(farm, worker_status="assigned", production_status="processing") == "running"
