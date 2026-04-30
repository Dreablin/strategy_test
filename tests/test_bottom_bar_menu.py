"""Bottom bar multi-level menu behavior."""

import pygame

from game.ui.bottom_bar import BUILD_MENU_SELECT, BottomBar


def test_bottom_bar_main_to_resource_to_back() -> None:
    surface = pygame.Surface((1200, 720))
    BottomBar._menu = "main"  # noqa: SLF001
    pygame.event.clear()

    # Main menu: first button opens Resource submenu.
    BottomBar.handle_click(surface, (100, 700))
    assert BottomBar._menu == "resource"  # noqa: SLF001

    # Resource submenu: first button is Back.
    BottomBar.handle_click(surface, (100, 700))
    assert BottomBar._menu == "main"  # noqa: SLF001
    assert not any(e.type == BUILD_MENU_SELECT for e in pygame.event.get())


def test_bottom_bar_dev_tree_posts_build_event() -> None:
    surface = pygame.Surface((1200, 720))
    BottomBar._menu = "dev"  # noqa: SLF001
    pygame.event.clear()

    # Dev menu layout: back, tree, stone.
    BottomBar.handle_click(surface, (500, 700))
    events = [e for e in pygame.event.get() if e.type == BUILD_MENU_SELECT]
    assert events
    assert events[-1].building_type == "DEV_TREE"


def test_bottom_bar_social_school_posts_build_event() -> None:
    surface = pygame.Surface((1200, 720))
    BottomBar._menu = "social"  # noqa: SLF001
    pygame.event.clear()
    # Social menu layout: back, school, house.
    BottomBar.handle_click(surface, (600, 700))
    events = [e for e in pygame.event.get() if e.type == BUILD_MENU_SELECT]
    assert events
    assert events[-1].building_type == "SCHOOL"


def test_bottom_bar_social_house_posts_build_event() -> None:
    surface = pygame.Surface((1200, 720))
    BottomBar._menu = "social"  # noqa: SLF001
    pygame.event.clear()
    BottomBar.handle_click(surface, (1000, 700))
    events = [e for e in pygame.event.get() if e.type == BUILD_MENU_SELECT]
    assert events
    assert events[-1].building_type == "HOUSE"


def test_bottom_bar_processing_sawmill_posts_build_event() -> None:
    surface = pygame.Surface((1200, 720))
    BottomBar._menu = "processing"  # noqa: SLF001
    pygame.event.clear()
    BottomBar.handle_click(surface, (1000, 700))
    events = [e for e in pygame.event.get() if e.type == BUILD_MENU_SELECT]
    assert events
    assert events[-1].building_type == "SAWMILL"
