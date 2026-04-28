"""Top bar population HUD tests."""

import pygame

from game.ui.top_bar import TopBar


def test_top_bar_layout_uses_population_label_format() -> None:
    surface = pygame.Surface((900, 700))
    layout = TopBar.layout(surface, current_population=3, max_population=8)
    assert layout.label == "3 (max 8)"


def test_top_bar_draw_renders_population_icon_in_header() -> None:
    surface = pygame.Surface((900, 700))
    TopBar.draw(surface, current_population=2, max_population=8)
    pixel = surface.get_at((18, 20))
    assert pixel[:3] != (32, 36, 44)
