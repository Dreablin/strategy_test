"""Tests for Winery panel shell routing and click actions (T356)."""

from __future__ import annotations

import pygame

from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.buildings.winery import Winery
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.ui.winery_panel import WineryPanel
from game.world import World


def _make_winery():
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    winery = registry.place(Winery, near_town_hall_tile(10, 10))
    winery.construction_site = None
    return winery


def test_winery_panel_supports_winery() -> None:
    winery = _make_winery()
    assert WineryPanel.supports_building(winery) is True


def test_winery_panel_does_not_support_town_hall() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    th = registry.place(TownHall, town_hall_origin_tile())
    assert WineryPanel.supports_building(th) is False


def test_winery_panel_layout_has_toggle() -> None:
    pygame.init()
    surface = pygame.Surface((800, 600))
    winery = _make_winery()
    layout = WineryPanel.layout(surface, winery, worker_assigned=False)
    assert layout.toggle is not None
    assert layout.toggle.width > 0
    pygame.quit()


def test_winery_panel_details_do_not_overlap_action_buttons() -> None:
    pygame.init()
    surface = pygame.Surface((800, 600))
    winery = _make_winery()
    layout = WineryPanel.layout(
        surface,
        winery,
        worker_assigned=True,
        production_status="processing",
    )
    details_top = WineryPanel.details_top(layout)
    details_bottom = details_top + 22 * 3 + 4 + 12
    action_tops = [layout.toggle.top]
    assert layout.upgrade is not None
    assert layout.demolish is not None
    action_tops.extend([layout.upgrade.top, layout.demolish.top])

    assert details_bottom < min(action_tops)
    pygame.quit()


def test_winery_panel_click_close() -> None:
    pygame.init()
    surface = pygame.Surface((800, 600))
    winery = _make_winery()
    layout = WineryPanel.layout(surface, winery, worker_assigned=False)
    action = WineryPanel.click_action(
        surface, layout.close.center, winery, worker_assigned=False
    )
    assert action == "close"
    pygame.quit()


def test_winery_panel_click_upgrade() -> None:
    pygame.init()
    surface = pygame.Surface((800, 600))
    winery = _make_winery()
    layout = WineryPanel.layout(surface, winery, worker_assigned=False)
    assert layout.upgrade is not None
    action = WineryPanel.click_action(
        surface, layout.upgrade.center, winery, worker_assigned=False
    )
    assert action == "upgrade"
    pygame.quit()


def test_winery_panel_click_demolish() -> None:
    pygame.init()
    surface = pygame.Surface((800, 600))
    winery = _make_winery()
    layout = WineryPanel.layout(surface, winery, worker_assigned=False)
    assert layout.demolish is not None
    action = WineryPanel.click_action(
        surface, layout.demolish.center, winery, worker_assigned=False
    )
    assert action == "demolish"
    pygame.quit()


def test_winery_panel_click_toggle_active() -> None:
    pygame.init()
    surface = pygame.Surface((800, 600))
    winery = _make_winery()
    layout = WineryPanel.layout(surface, winery, worker_assigned=False)
    action = WineryPanel.click_action(
        surface, layout.toggle.center, winery, worker_assigned=False
    )
    assert action == "toggle_active"
    pygame.quit()


def test_winery_panel_toggle_label() -> None:
    winery = _make_winery()
    assert WineryPanel.toggle_label(winery) == "Active"
    winery.set_active(False)
    assert WineryPanel.toggle_label(winery) == "Inactive"
