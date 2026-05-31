"""Bottom bar menu contracts."""

import pygame

from game import i18n
from game.ui.bottom_bar import (
    BUILD_MENU_SELECT,
    BottomBar,
    _FOOD_BUTTON_SPECS,
    _RESOURCE_BUTTON_SPECS,
    _button_rects,
    _construction_cost_lines,
    _hovered_building_tag,
    _labeled_menu_buttons,
)
from game.ui.building_panel import building_display_name


def _building_tags(specs: tuple[tuple[str, str], ...]) -> set[str]:
    return {tag for _asset, tag in specs}


def test_bottom_bar_resource_menu_contains_resource_buildings_only() -> None:
    assert _building_tags(_RESOURCE_BUTTON_SPECS) == {
        "LUMBER_CAMP",
        "STONE_MINE",
        "IRON_MINE",
        "FORESTER_HUT",
        "WELL",
    }


def test_bottom_bar_food_menu_contains_food_buildings() -> None:
    assert _building_tags(_FOOD_BUTTON_SPECS) == {
        "FARM",
        "FIELD",
        "VINEYARD_FARM",
        "VINEYARD",
    }


def test_bottom_bar_main_can_open_food_menu_and_go_back() -> None:
    surface = pygame.Surface((1200, 720))
    BottomBar._menu = "main"  # noqa: SLF001
    pygame.event.clear()

    # Main menu has five equal columns: Resource, Food, Social, Processing, Dev.
    BottomBar.handle_click(surface, (360, 700))
    assert BottomBar._menu == "food"  # noqa: SLF001

    BottomBar.handle_click(surface, (100, 700))
    assert BottomBar._menu == "main"  # noqa: SLF001
    assert not any(e.type == BUILD_MENU_SELECT for e in pygame.event.get())


def test_bottom_bar_back_to_main_returns_from_submenu() -> None:
    BottomBar._menu = "social"  # noqa: SLF001

    assert BottomBar.back_to_main() is True
    assert BottomBar._menu == "main"  # noqa: SLF001
    assert BottomBar.back_to_main() is False


def test_bottom_bar_posts_selected_food_building_event() -> None:
    surface = pygame.Surface((1200, 720))
    BottomBar._menu = "food"  # noqa: SLF001
    pygame.event.clear()

    BottomBar.handle_click(surface, (600, 700))

    events = [e for e in pygame.event.get() if e.type == BUILD_MENU_SELECT]
    assert events
    assert events[-1].building_type == "FIELD"


def test_bottom_bar_processing_menu_posts_winery_event() -> None:
    surface = pygame.Surface((1200, 720))
    BottomBar._menu = "processing"  # noqa: SLF001
    pygame.event.clear()

    rects = _button_rects(surface, 7)
    winery_center = rects[6].center
    BottomBar.handle_click(surface, winery_center)

    events = [e for e in pygame.event.get() if e.type == BUILD_MENU_SELECT]
    assert events
    assert events[-1].building_type == "WINERY"


def test_bottom_bar_hover_detects_building_button() -> None:
    surface = pygame.Surface((1200, 720))
    BottomBar._menu = "resource"  # noqa: SLF001
    rects = _button_rects(surface, 6)

    assert _hovered_building_tag(surface, rects[1].center) == "LUMBER_CAMP"
    assert _hovered_building_tag(surface, rects[0].center) is None


def test_bottom_bar_cost_tooltip_uses_construction_requirements() -> None:
    lines = _construction_cost_lines("LUMBER_CAMP")
    assert lines[0] == f"{i18n.t('ui.common.cost')}:"
    assert any(line.startswith(f"{i18n.t('resource.wood')}:") for line in lines)


def test_bottom_bar_statue_tooltip_shows_excavation_research_requirement() -> None:
    lines = _construction_cost_lines("STATUE")

    assert i18n.t("ui.common.requires_research", name="Excavation Plans") in lines


def test_bottom_bar_building_labels_use_locale_names_en() -> None:
    labeled = _labeled_menu_buttons(_RESOURCE_BUTTON_SPECS)
    lumber = next(label for _asset, label, tag in labeled if tag == "LUMBER_CAMP")
    assert lumber == building_display_name("LUMBER_CAMP")
    assert lumber == "Lumber Camp"


def test_bottom_bar_building_labels_ru_smoke(use_locale) -> None:
    with use_locale("ru"):
        labeled = _labeled_menu_buttons(_RESOURCE_BUTTON_SPECS)
        lumber = next(label for _asset, label, tag in labeled if tag == "LUMBER_CAMP")
        assert lumber == "Лагерь лесорубов"
        lines = _construction_cost_lines("LUMBER_CAMP")
        assert lines[0] == f"{i18n.t('ui.common.cost')}:"


def test_bottom_bar_statue_menu_uses_final_stage_sprite(monkeypatch) -> None:
    surface = pygame.Surface((1200, 720))
    BottomBar._menu = "social"  # noqa: SLF001
    calls: list[tuple[str, int]] = []

    def fake_building_sprite(asset_key: str, level: int):
        calls.append((asset_key, level))
        return pygame.Surface((40, 32), pygame.SRCALPHA)

    monkeypatch.setattr("game.ui.bottom_bar.building_sprite", fake_building_sprite)

    BottomBar.draw(surface)

    assert ("statue", 4) in calls
    assert ("statue", 1) not in calls


def test_bottom_bar_draws_cost_tooltip_on_building_hover() -> None:
    surface = pygame.Surface((1200, 720))
    surface.fill((10, 12, 16))
    BottomBar._menu = "resource"  # noqa: SLF001
    hover = _button_rects(surface, 6)[1].center

    BottomBar.draw(surface, hover_pos=hover)

    assert surface.get_at((hover[0] + 18, surface.get_height() - 118))[:3] != (10, 12, 16)
