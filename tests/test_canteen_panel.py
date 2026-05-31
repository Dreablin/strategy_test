"""Canteen panel: layout, storage lines, toggle, upgrade/demolish, blocked hints."""

from __future__ import annotations

import pygame

from game import i18n
from game.buildings.canteen import Canteen
from game.canteen_dining import try_reserve_diner_slot
from game.ui.canteen_panel import CanteenPanel
from game.ui.panel_i18n import resource_amount_line
from game.worker_models import Worker


def test_canteen_panel_storage_lines_use_locale() -> None:
    canteen = Canteen(level=1, grid_pos=(10, 10))
    canteen.add_local_storage("chicken", 2)
    chicken, bread, water, meal = CanteenPanel.storage_lines(canteen)
    assert chicken == resource_amount_line("chicken", 2, canteen.local_storage_capacity("chicken"))
    assert i18n.t("resource.simple_meal") in meal


def test_canteen_panel_storage_lines_ru(use_locale) -> None:
    canteen = Canteen(level=1, grid_pos=(10, 10))
    with use_locale("ru"):
        _chicken, _bread, _water, meal = CanteenPanel.storage_lines(canteen)
        assert i18n.t("resource.simple_meal") in meal
        assert "Простая еда" in meal


def test_canteen_panel_supports_building_and_toggle_click() -> None:
    surface = pygame.Surface((1280, 720))
    canteen = Canteen(level=1, grid_pos=(10, 10))
    layout = CanteenPanel.layout(surface, canteen, worker_assigned=False, production_status="no_worker")
    assert CanteenPanel.supports_building(canteen) is True
    assert layout.upgrade is not None
    assert layout.demolish is not None
    assert (
        CanteenPanel.click_action(
            surface,
            layout.toggle.center,
            canteen,
            worker_assigned=False,
            production_status="no_worker",
        )
        == "toggle_active"
    )


def test_canteen_panel_upgrade_and_demolish_click() -> None:
    surface = pygame.Surface((1280, 720))
    canteen = Canteen(level=1, grid_pos=(10, 10))
    layout = CanteenPanel.layout(surface, canteen, worker_assigned=False, production_status="no_worker")
    assert CanteenPanel.click_action(surface, layout.upgrade.center, canteen, worker_assigned=False, production_status="no_worker") == "upgrade"
    assert CanteenPanel.click_action(surface, layout.demolish.center, canteen, worker_assigned=False, production_status="no_worker") == "demolish"


def test_canteen_panel_blocked_reason_hints() -> None:
    canteen = Canteen(level=1, grid_pos=(10, 10))
    assert (
        CanteenPanel.blocked_reason(canteen, worker_status="empty", production_status="no_worker") == "no worker"
    )
    canteen.set_active(False)
    assert CanteenPanel.blocked_reason(canteen, worker_status="assigned", production_status="inactive") == "inactive"
    canteen.set_active(True)
    canteen.add_local_storage("chicken", 1)
    canteen.add_local_storage("bread", 1)
    canteen.add_local_storage("water", 1)
    canteen.add_local_storage("simple_meal", canteen.local_storage_capacity("simple_meal"))
    assert (
        CanteenPanel.blocked_reason(canteen, worker_status="assigned", production_status="output_full")
        == "output full"
    )
    canteen.take_local_storage("simple_meal", canteen.local_storage_capacity("simple_meal"))
    assert CanteenPanel.blocked_reason(canteen, worker_status="assigned", production_status="resting") == "resting"
    assert CanteenPanel.blocked_reason(canteen, worker_status="assigned", production_status="processing") == "running"


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
        production_status="processing",
        now_ms=mid,
    )
    layout = CanteenPanel.layout(surface, canteen, worker_assigned=True, production_status="processing")
    bar_center_x = layout.frame.left + layout.frame.width // 2
    bar_sample_y = layout.frame.bottom - 80
    c = surface.get_at((bar_center_x, bar_sample_y))
    assert c.r > 80 or c.g > 80 or c.b > 80


def test_canteen_panel_layout_has_one_diner_tile_per_slot() -> None:
    surface = pygame.Surface((1280, 720))
    canteen = Canteen(level=3, grid_pos=(10, 10))
    layout = CanteenPanel.layout(surface, canteen, worker_assigned=True, production_status="processing")
    tiles = CanteenPanel._diner_tiles(layout, canteen.diner_slot_capacity())
    assert len(tiles) == canteen.diner_slot_capacity()
    assert len({(t.x, t.y, t.w, t.h) for t in tiles}) == len(tiles)
    progress_bar_bottom = layout.frame.top + 16 + 4 * 26 + 32 + 5 * 22 + 12
    assert all(tile.top > progress_bar_bottom for tile in tiles)
    assert layout.upgrade is not None
    assert all(tile.bottom < layout.upgrade.top for tile in tiles)

    high_level = Canteen(level=10, grid_pos=(10, 10))
    high_layout = CanteenPanel.layout(surface, high_level, worker_assigned=True, production_status="processing")
    high_tiles = CanteenPanel._diner_tiles(high_layout, high_level.diner_slot_capacity())
    assert high_layout.upgrade is None
    assert high_layout.demolish is not None
    assert all(tile.bottom < high_layout.demolish.top for tile in high_tiles)


def test_canteen_panel_draws_reserved_diner_worker_and_eating_progress() -> None:
    surface = pygame.Surface((1280, 720))
    canteen = Canteen(level=1, grid_pos=(10, 10))
    worker = Worker("BAKER", stand_tile=(12, 12))
    assert try_reserve_diner_slot(canteen, worker)
    worker.dining_phase = "eating"
    worker.dining_eating_started_ms = 10_000
    now_ms = 20_000

    CanteenPanel.draw(
        surface,
        canteen,
        worker_assigned=True,
        worker_status="assigned",
        production_status="processing",
        now_ms=now_ms,
    )
    layout = CanteenPanel.layout(surface, canteen, worker_assigned=True, production_status="processing")
    tiles = CanteenPanel._diner_tiles(layout, canteen.diner_slot_capacity())
    tile = tiles[0]
    inside = surface.get_at((tile.left + 3, tile.top + 3))
    assert inside.r > 40 or inside.g > 40 or inside.b > 40
    progress = surface.get_at((tile.left + 2, tile.bottom - 3))
    assert progress.r > 120


def test_canteen_panel_click_inside_diner_tile_keeps_panel_open() -> None:
    surface = pygame.Surface((1280, 720))
    canteen = Canteen(level=1, grid_pos=(10, 10))
    layout = CanteenPanel.layout(surface, canteen, worker_assigned=True, production_status="processing")
    tile = CanteenPanel._diner_tiles(layout, canteen.diner_slot_capacity())[0]
    assert (
        CanteenPanel.click_action(
            surface,
            tile.center,
            canteen,
            worker_assigned=True,
            production_status="processing",
        )
        is None
    )
