"""Building modal panel layout and click routing."""

import pygame

from game import i18n
from game.buildings.lumber_camp import LumberCamp
from game.buildings.school import School
from game.buildings.statue import Statue
from game.buildings.town_hall import TownHall
from game.buildings.well import Well
from game.ui.building_panel import (
    BuildingPanel,
    building_display_name,
    building_description,
    _upgrade_cost_lines,
    _upgrade_label,
    draw_upgrade_cost_tooltip,
    worker_status_line,
)


def test_building_panel_close_click() -> None:
    surface = pygame.Surface((640, 480))
    building = LumberCamp(level=2, grid_pos=(4, 4))
    layout = BuildingPanel.layout(surface, building, worker_assigned=False)
    cx, cy = layout.close.center
    assert BuildingPanel.click_action(surface, (cx, cy), building, worker_assigned=False) == "close"


def test_building_panel_demolish_click() -> None:
    surface = pygame.Surface((640, 480))
    building = LumberCamp(level=1, grid_pos=(4, 4))
    layout = BuildingPanel.layout(surface, building, worker_assigned=False)
    assert layout.demolish is not None
    cx, cy = layout.demolish.center
    assert BuildingPanel.click_action(surface, (cx, cy), building, worker_assigned=False) == "demolish"


def test_building_panel_upgrade_enabled_even_when_poor() -> None:
    surface = pygame.Surface((640, 480))
    building = LumberCamp(level=1, grid_pos=(4, 4))
    layout = BuildingPanel.layout(surface, building, worker_assigned=False)
    assert layout.upgrade is not None
    assert layout.upgrade_enabled is True
    cx, cy = layout.upgrade.center
    assert BuildingPanel.click_action(surface, (cx, cy), building, worker_assigned=False) == "upgrade"


def test_building_panel_upgrade_label_does_not_claim_free() -> None:
    building = LumberCamp(level=1, grid_pos=(4, 4))
    assert _upgrade_label(building) == i18n.t("ui.building.upgrade_level", level=2)
    assert i18n.t("ui.common.free") not in _upgrade_label(building)


def test_building_panel_upgrade_label_for_statue_stage() -> None:
    statue = Statue(level=1, grid_pos=(4, 4))
    assert _upgrade_label(statue) == i18n.t("ui.statue.start_stage", stage="Foundation")


def test_building_panel_upgrade_tooltip_uses_construction_requirements() -> None:
    building = LumberCamp(level=1, grid_pos=(4, 4))
    lines = _upgrade_cost_lines(building)
    assert lines[0] == f"{i18n.t('ui.building.upgrade_cost')}:"
    assert any(line.startswith(f"{i18n.t('resource.wood')}:") for line in lines)


def test_building_panel_draws_upgrade_cost_tooltip_on_hover() -> None:
    surface = pygame.Surface((800, 600))
    building = LumberCamp(level=1, grid_pos=(4, 4))
    layout = BuildingPanel.layout(surface, building, worker_assigned=False)
    box = draw_upgrade_cost_tooltip(surface, building, layout.upgrade, hover_pos=layout.upgrade.center)
    assert box is not None
    assert surface.get_at(box.center)[:3] != (0, 0, 0)


def test_building_panel_draw_smoke() -> None:
    surface = pygame.Surface((800, 600))
    building = LumberCamp(level=3, grid_pos=(2, 2))
    BuildingPanel.draw(surface, building, worker_assigned=True)
    assert surface.get_at((400, 300)) != (0, 0, 0, 255)


def test_building_panel_shows_upgrade_for_town_hall() -> None:
    surface = pygame.Surface((640, 480))
    building = TownHall(level=1, grid_pos=(10, 10))
    layout = BuildingPanel.layout(surface, building, worker_assigned=False)
    assert layout.upgrade is not None


def test_layout_grows_when_production_status_line_is_present() -> None:
    surface = pygame.Surface((800, 600))
    building = LumberCamp(level=1, grid_pos=(4, 4))

    without_status = BuildingPanel.layout(
        surface,
        building,
        worker_assigned=True,
    )
    with_status = BuildingPanel.layout(
        surface,
        building,
        worker_assigned=True,
        production_status="Resting",
    )

    assert with_status.frame.height > without_status.frame.height


def test_worker_status_line_includes_building_worker_name() -> None:
    assert worker_status_line(Well(level=2, grid_pos=(4, 4)), "assigned") == "Worker (Waterman): assigned"
    assert worker_status_line(LumberCamp(level=1, grid_pos=(4, 4)), "on the way") == "Worker (Lumberjack): on the way"


def test_worker_status_line_omits_name_for_unstaffed_buildings() -> None:
    assert worker_status_line(School(level=1, grid_pos=(4, 4)), "empty") == "Worker: empty"


def test_town_hall_localized_name_and_description_en() -> None:
    assert building_display_name("TOWN_HALL") == "Town Hall"
    assert building_description("TOWN_HALL") == "The heart of your settlement."


def test_laboratory_localized_name_and_description_en() -> None:
    assert building_display_name("LABORATORY") == "Laboratory"
    description = building_description("LABORATORY")
    assert description
    assert "research" in description.lower()
    assert "scientist" in description.lower()


def test_statue_localized_name_and_description_en() -> None:
    assert building_display_name("STATUE") == "Statue"
    assert "four stages" in building_description("STATUE").lower()


def test_town_hall_localized_name_ru(use_locale) -> None:
    with use_locale("ru"):
        assert building_display_name("TOWN_HALL") == "Ратуша"
