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
    camp = LumberCamp(level=1, grid_pos=(10, 10))

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
    camp = LumberCamp(level=1, grid_pos=(10, 10))
    camp.record_wood_delivered(7)

    assert LumberCampPanel.delivered_line(camp) == "Wood delivered: 7"


def test_lumber_camp_panel_storage_line_reflects_stored_and_capacity() -> None:
    camp = LumberCamp(level=1, grid_pos=(10, 10))
    camp.add_to_storage(2)
    assert LumberCampPanel.storage_line(camp) == "Storage: 2 / 3"

    camp.level = 3
    assert LumberCampPanel.storage_line(camp) == "Storage: 2 / 7"


def test_non_lumber_buildings_do_not_expose_toggle_or_counter() -> None:
    others = [
        Farm(level=1, grid_pos=(2, 2)),
        StoneMine(level=1, grid_pos=(4, 4)),
        IronMine(level=1, grid_pos=(6, 6)),
    ]
    for b in others:
        assert not LumberCampPanel.supports_building(b)


def test_lumber_camp_click_upgrade_returns_upgrade_not_demolish() -> None:
    """Regression: clicking the visible Upgrade button on the LumberCamp panel
    must not be misinterpreted as Demolish (which made the camp vanish on level-up).

    The panel is drawn with extra_bottom_px=72 to fit the toggle row, so hit
    detection must use the same extended frame.
    """
    surface = pygame.Surface((1280, 720))
    camp = LumberCamp(level=1, grid_pos=(10, 10))
    resources = ResourceManager()
    resources.add("wood", 1000)
    resources.add("stone", 1000)
    resources.add("iron", 1000)

    layout = LumberCampPanel.layout(surface, camp, resources, worker_assigned=False)
    assert layout.upgrade is not None, "panel must expose an Upgrade button at L1"

    for offset_y in (0, layout.upgrade.height // 2 - 1, -(layout.upgrade.height // 2 - 1)):
        click = (layout.upgrade.centerx, layout.upgrade.centery + offset_y)
        action = LumberCampPanel.click_action(
            surface, click, camp, resources, worker_assigned=False
        )
        assert action == "upgrade", (
            f"click anywhere inside the visible Upgrade button must return 'upgrade', "
            f"got {action!r} at offset_y={offset_y}"
        )


def test_lumber_camp_click_demolish_still_returns_demolish() -> None:
    """Negative companion: clicking the Demolish button still works correctly."""
    surface = pygame.Surface((1280, 720))
    camp = LumberCamp(level=1, grid_pos=(10, 10))
    resources = ResourceManager()

    layout = LumberCampPanel.layout(surface, camp, resources, worker_assigned=False)
    assert layout.demolish is not None
    click = (layout.demolish.centerx, layout.demolish.centery)
    action = LumberCampPanel.click_action(surface, click, camp, resources, worker_assigned=False)
    assert action == "demolish"
