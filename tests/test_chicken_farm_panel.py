"""Chicken farm panel layout, click actions, and blocked hints."""

from __future__ import annotations

import pygame

from game import i18n
from game.buildings.chicken_farm import ChickenFarm
from game.ui.chicken_farm_panel import ChickenFarmPanel
from game.ui.panel_i18n import flow_line


def test_chicken_farm_panel_storage_lines_use_locale() -> None:
    farm = ChickenFarm(level=1, grid_pos=(10, 10))
    farm.add_wheat_in(1)
    farm.add_water_in(2)
    wheat, water, chicken = ChickenFarmPanel.storage_lines(farm)
    assert wheat == flow_line(
        role_key="ui.panel.input", resource_key="wheat", amount=1, capacity=farm.input_capacity()
    )
    assert i18n.t("resource.chicken") in chicken


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
