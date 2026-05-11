"""Bottom bar menu contracts."""

import pygame

from game.ui.bottom_bar import (
    BUILD_MENU_SELECT,
    BottomBar,
    _FOOD_BUTTONS,
    _RESOURCE_BUTTONS,
)


def _building_tags(entries: tuple[tuple[str, str, str], ...]) -> set[str]:
    return {tag for _asset, _label, tag in entries}


def test_bottom_bar_resource_menu_contains_resource_buildings_only() -> None:
    assert _building_tags(_RESOURCE_BUTTONS) == {
        "LUMBER_CAMP",
        "STONE_MINE",
        "IRON_MINE",
        "FORESTER_HUT",
        "WELL",
    }


def test_bottom_bar_food_menu_contains_food_buildings() -> None:
    assert _building_tags(_FOOD_BUTTONS) == {
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


def test_bottom_bar_posts_selected_food_building_event() -> None:
    surface = pygame.Surface((1200, 720))
    BottomBar._menu = "food"  # noqa: SLF001
    pygame.event.clear()

    BottomBar.handle_click(surface, (600, 700))

    events = [e for e in pygame.event.get() if e.type == BUILD_MENU_SELECT]
    assert events
    assert events[-1].building_type == "FIELD"
