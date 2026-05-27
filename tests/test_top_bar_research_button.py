"""Top-bar Research button visibility tests (T408)."""

from __future__ import annotations

import pygame

from game.buildings.laboratory import Laboratory
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.laboratory_visibility import has_completed_laboratory
from game.ui.top_bar import TopBar
from game.world import World


def _registry_with_laboratory(*, completed: bool) -> BuildingRegistry:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    laboratory = registry.place(Laboratory, near_town_hall_tile(10, 10))
    if completed:
        laboratory.construction_site = None
    return registry


def test_has_completed_laboratory_false_without_laboratory() -> None:
    registry = BuildingRegistry(World(world_seed=0))
    registry.place(TownHall, town_hall_origin_tile())
    assert has_completed_laboratory(registry) is False


def test_has_completed_laboratory_false_while_under_construction() -> None:
    registry = _registry_with_laboratory(completed=False)
    laboratory = next(b for b in registry.all() if b.type_tag == "LABORATORY")
    assert laboratory.is_under_construction
    assert has_completed_laboratory(registry) is False


def test_has_completed_laboratory_true_when_built() -> None:
    registry = _registry_with_laboratory(completed=True)
    assert has_completed_laboratory(registry) is True


def test_top_bar_hides_research_button_without_laboratory() -> None:
    surface = pygame.Surface((900, 700))
    layout = TopBar.layout(
        surface,
        current_population=1,
        max_population=4,
        show_research_button=False,
    )
    assert layout.research_button is None


def test_top_bar_shows_research_button_when_requested() -> None:
    surface = pygame.Surface((900, 700))
    layout = TopBar.layout(
        surface,
        current_population=1,
        max_population=4,
        show_research_button=True,
    )
    assert layout.research_button is not None
    assert layout.research_button.width > 0
    assert layout.research_button.bottom <= 48
    assert layout.research_button.right < dev_asset_reload_button_right(surface)


def dev_asset_reload_button_right(surface: pygame.Surface) -> int:
    from game import dev_asset_reload

    return dev_asset_reload.button_rect(surface).left


def test_top_bar_draw_research_button_pixels_differ_from_bar_background() -> None:
    surface = pygame.Surface((900, 700))
    bg = (32, 36, 44)
    TopBar.draw(
        surface,
        current_population=2,
        max_population=8,
        show_research_button=True,
    )
    layout = TopBar.layout(
        surface,
        current_population=2,
        max_population=8,
        show_research_button=True,
    )
    assert layout.research_button is not None
    center = layout.research_button.center
    pixel = surface.get_at(center)
    assert pixel[:3] != bg


def test_top_bar_draw_without_research_button_leaves_button_area_as_bar() -> None:
    surface = pygame.Surface((900, 700))
    layout_hidden = TopBar.layout(
        surface,
        current_population=2,
        max_population=8,
        show_research_button=False,
    )
    TopBar.draw(
        surface,
        current_population=2,
        max_population=8,
        show_research_button=True,
    )
    layout_shown = TopBar.layout(
        surface,
        current_population=2,
        max_population=8,
        show_research_button=True,
    )
    assert layout_hidden.research_button is None
    assert layout_shown.research_button is not None
    probe_x = layout_shown.research_button.centerx
    probe_y = layout_shown.research_button.centery
    TopBar.draw(
        surface,
        current_population=2,
        max_population=8,
        show_research_button=False,
    )
    hidden_pixel = surface.get_at((probe_x, probe_y))
    assert hidden_pixel[:3] == (32, 36, 44)
