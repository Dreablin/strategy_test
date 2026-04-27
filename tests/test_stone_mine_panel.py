"""Failing UI tests for Stone Mine panel toggle/counter/storage (T120)."""

import pygame

from game.buildings.farm import Farm
from game.buildings.iron_mine import IronMine
from game.buildings.lumber_camp import LumberCamp
from game.buildings.stone_mine import StoneMine
from game.resources import ResourceManager
from game.ui.stone_mine_panel import StoneMinePanel


def test_stone_mine_layout_exposes_toggle_rect() -> None:
    surface = pygame.Surface((800, 600))
    mine = StoneMine(level=1, grid_pos=(10, 10))
    resources = ResourceManager()

    layout = StoneMinePanel.layout(surface, mine, resources, worker_assigned=False)

    assert layout.toggle is not None


def test_stone_mine_toggle_label_reflects_active_state() -> None:
    mine = StoneMine(level=1, grid_pos=(10, 10))

    mine.set_active(True)
    assert StoneMinePanel.toggle_label(mine) == "Active"
    mine.set_active(False)
    assert StoneMinePanel.toggle_label(mine) == "Inactive"


def test_stone_mine_click_toggle_returns_toggle_action() -> None:
    surface = pygame.Surface((800, 600))
    mine = StoneMine(level=1, grid_pos=(10, 10))
    resources = ResourceManager()
    layout = StoneMinePanel.layout(surface, mine, resources, worker_assigned=False)
    cx, cy = layout.toggle.center

    action = StoneMinePanel.click_action(surface, (cx, cy), mine, resources, worker_assigned=False)

    assert action == "toggle_active"


def test_stone_mine_panel_shows_delivered_counter_line() -> None:
    mine = StoneMine(level=1, grid_pos=(10, 10))
    mine.record_stone_delivered(9)

    assert StoneMinePanel.delivered_line(mine) == "Stones delivered: 9"


def test_stone_mine_panel_storage_line_reflects_stored_and_capacity() -> None:
    mine = StoneMine(level=1, grid_pos=(10, 10))
    mine.add_to_storage(2)
    assert StoneMinePanel.storage_line(mine) == "Storage: 2 / 3"

    mine.level = 3
    assert StoneMinePanel.storage_line(mine) == "Storage: 2 / 7"


def test_non_stone_mine_buildings_do_not_use_stone_mine_panel() -> None:
    others = [
        LumberCamp(level=1, grid_pos=(2, 2)),
        Farm(level=1, grid_pos=(4, 4)),
        IronMine(level=1, grid_pos=(6, 6)),
    ]
    for b in others:
        assert not StoneMinePanel.supports_building(b)
