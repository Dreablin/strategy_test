"""Failing tests for Lumber Camp panel toggle/counter UI (T88)."""

import pygame

from game.buildings.farm import Farm
from game.buildings.iron_mine import IronMine
from game.buildings.lumber_camp import LumberCamp
from game.buildings.stone_mine import StoneMine
from game.resources import ResourceManager
from game.ui.lumber_camp_panel import LumberCampPanel


def test_lumber_camp_layout_exposes_toggle_rect() -> None:
    surface = pygame.Surface((800, 600))
    camp = LumberCamp(level=1, grid_pos=(10, 10))
    resources = ResourceManager()

    layout = LumberCampPanel.layout(surface, camp, resources, worker_assigned=False)

    assert layout.toggle is not None


def test_lumber_camp_toggle_label_reflects_active_state() -> None:
    surface = pygame.Surface((800, 600))
    camp = LumberCamp(level=1, grid_pos=(10, 10))
    resources = ResourceManager()

    camp.set_active(True)
    assert LumberCampPanel.toggle_label(camp) == "Active"
    camp.set_active(False)
    assert LumberCampPanel.toggle_label(camp) == "Inactive"


def test_lumber_camp_click_toggle_returns_toggle_action() -> None:
    surface = pygame.Surface((800, 600))
    camp = LumberCamp(level=1, grid_pos=(10, 10))
    resources = ResourceManager()
    layout = LumberCampPanel.layout(surface, camp, resources, worker_assigned=False)
    cx, cy = layout.toggle.center

    action = LumberCampPanel.click_action(surface, (cx, cy), camp, resources, worker_assigned=False)

    assert action == "toggle_active"


def test_lumber_camp_panel_shows_delivered_counter_line() -> None:
    surface = pygame.Surface((800, 600))
    camp = LumberCamp(level=1, grid_pos=(10, 10))
    resources = ResourceManager()
    camp.record_wood_delivered(7)

    assert LumberCampPanel.delivered_line(camp) == "Wood delivered: 7"


def test_non_lumber_buildings_do_not_expose_toggle_or_counter() -> None:
    others = [
        Farm(level=1, grid_pos=(2, 2)),
        StoneMine(level=1, grid_pos=(4, 4)),
        IronMine(level=1, grid_pos=(6, 6)),
    ]
    for b in others:
        assert not LumberCampPanel.supports_building(b)
