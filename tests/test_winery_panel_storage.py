"""Tests for Winery panel storage/progress rows (T357)."""

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


def test_storage_lines_empty() -> None:
    winery = _make_winery()
    grapes_line, wine_line = WineryPanel.storage_lines(winery)
    assert "0" in grapes_line and "3" in grapes_line
    assert "0" in wine_line and "3" in wine_line


def test_storage_lines_with_stock() -> None:
    winery = _make_winery()
    winery.add_grapes(2)
    winery.add_wine(1)
    grapes_line, wine_line = WineryPanel.storage_lines(winery)
    assert "2" in grapes_line
    assert "1" in wine_line


def test_draw_does_not_crash() -> None:
    pygame.init()
    surface = pygame.Surface((800, 600))
    winery = _make_winery()
    winery.add_grapes(2)
    WineryPanel.draw(
        surface,
        winery,
        worker_assigned=True,
        worker_status="assigned",
        production_status="Processing",
        now_ms=5000,
    )
    pygame.quit()


def test_draw_with_progress_bar() -> None:
    pygame.init()
    surface = pygame.Surface((800, 600))
    winery = _make_winery()
    winery.add_grapes(3)
    winery.processing_started_ms = 1000
    WineryPanel.draw(
        surface,
        winery,
        worker_assigned=True,
        worker_status="assigned",
        production_status="Processing",
        now_ms=31000,
    )
    pygame.quit()


def test_layout_toggle_not_overlapping_demolish() -> None:
    pygame.init()
    surface = pygame.Surface((800, 600))
    winery = _make_winery()
    layout = WineryPanel.layout(surface, winery, worker_assigned=False)
    if layout.demolish is not None:
        assert not layout.toggle.colliderect(layout.demolish)
    pygame.quit()
