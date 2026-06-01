"""Top bar population HUD tests."""

import pygame

from game import i18n
from game.ui.top_bar import TopBar


def test_top_bar_layout_uses_population_label_format() -> None:
    surface = pygame.Surface((900, 700))
    layout = TopBar.layout(
        surface,
        current_population=3,
        max_population=8,
        delivery_queue_size=5,
        active_delivery_count=2,
    )
    assert layout.label == i18n.t("ui.topbar.population", current=3, max=8)
    assert layout.delivery_label == i18n.t("ui.topbar.deliveries", n=5, k=2)
    assert layout.delivery_pos[0] > layout.population_button.right
    assert layout.population_button.colliderect(layout.icon_rect)
    assert layout.population_button.collidepoint(layout.label_pos)


def test_top_bar_layout_templates_ru(use_locale) -> None:
    surface = pygame.Surface((900, 700))
    with use_locale("ru"):
        layout = TopBar.layout(
            surface,
            current_population=3,
            max_population=8,
            delivery_queue_size=5,
            active_delivery_count=2,
            show_research_button=True,
        )
        assert layout.label == i18n.t("ui.topbar.population", current=3, max=8)
        assert layout.delivery_label == i18n.t("ui.topbar.deliveries", n=5, k=2)
        assert layout.research_button is not None


def test_top_bar_draw_renders_population_icon_in_header() -> None:
    surface = pygame.Surface((900, 700))
    TopBar.draw(surface, current_population=2, max_population=8, delivery_queue_size=3, active_delivery_count=1)
    pixel = surface.get_at((18, 20))
    assert pixel[:3] != (32, 36, 44)
