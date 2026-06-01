"""Fixed-height top HUD strip for population totals."""

from __future__ import annotations

from dataclasses import dataclass

import pygame

from game import dev_asset_reload, i18n
from game.assets import population_icon
from game.ui.fonts import ui_font

_BAR_HEIGHT = 48
_RESEARCH_BTN_W = 96
_RESEARCH_GAP = 18


def _population_label(current_population: int, max_population: int) -> str:
    return i18n.t(
        "ui.topbar.population",
        current=int(current_population),
        max=int(max_population),
    )


def _delivery_label(delivery_queue_size: int, active_delivery_count: int) -> str:
    return i18n.t(
        "ui.topbar.deliveries",
        n=max(0, int(delivery_queue_size)),
        k=max(0, int(active_delivery_count)),
    )


def _research_button_label() -> str:
    return i18n.t("ui.topbar.research")


def research_button_visible(registry: object | None) -> bool:
    """Whether the top-bar Research control should be shown for *registry*."""
    if registry is None:
        return False
    from game.laboratory_visibility import has_completed_laboratory

    return has_completed_laboratory(registry)


@dataclass(frozen=True, slots=True)
class TopBarLayout:
    bar_rect: pygame.Rect
    icon_rect: pygame.Rect
    population_button: pygame.Rect
    delivery_label: str
    delivery_pos: tuple[int, int]
    label: str
    label_pos: tuple[int, int]
    research_button: pygame.Rect | None


class TopBar:
    """48 px strip: `[population icon] current (max N)`."""

    @staticmethod
    def layout(
        surface: pygame.Surface,
        *,
        current_population: int,
        max_population: int,
        delivery_queue_size: int = 0,
        active_delivery_count: int = 0,
        show_research_button: bool = False,
    ) -> TopBarLayout:
        width = surface.get_width()
        bar_rect = pygame.Rect(0, 0, width, _BAR_HEIGHT)
        icon = population_icon()
        icon_x = 10
        icon_y = (_BAR_HEIGHT - icon.get_height()) // 2
        icon_rect = pygame.Rect(icon_x, icon_y, icon.get_width(), icon.get_height())
        label = _population_label(current_population, max_population)
        label_pos = (icon_rect.right + 8, (_BAR_HEIGHT - 22) // 2)
        font = ui_font(22)
        label_w, _label_h = font.size(label)
        population_button = pygame.Rect(
            icon_rect.left - 6,
            6,
            icon.get_width() + 8 + label_w + 12,
            _BAR_HEIGHT - 12,
        )
        delivery_label = _delivery_label(delivery_queue_size, active_delivery_count)
        delivery_pos = (population_button.right + 18, label_pos[1])
        research_button: pygame.Rect | None = None
        if show_research_button:
            delivery_w, _ = font.size(delivery_label)
            research_x = delivery_pos[0] + delivery_w + _RESEARCH_GAP
            research_button = pygame.Rect(
                research_x,
                6,
                _RESEARCH_BTN_W,
                _BAR_HEIGHT - 12,
            )
        return TopBarLayout(
            bar_rect=bar_rect,
            icon_rect=icon_rect,
            population_button=population_button,
            delivery_label=delivery_label,
            delivery_pos=delivery_pos,
            label=label,
            label_pos=label_pos,
            research_button=research_button,
        )

    @staticmethod
    def draw(
        surface: pygame.Surface,
        *,
        current_population: int,
        max_population: int,
        delivery_queue_size: int = 0,
        active_delivery_count: int = 0,
        show_research_button: bool = False,
    ) -> None:
        layout = TopBar.layout(
            surface,
            current_population=current_population,
            max_population=max_population,
            delivery_queue_size=delivery_queue_size,
            active_delivery_count=active_delivery_count,
            show_research_button=show_research_button,
        )
        pygame.draw.rect(surface, (32, 36, 44), layout.bar_rect)
        pygame.draw.line(
            surface,
            (56, 60, 68),
            (0, _BAR_HEIGHT - 1),
            (layout.bar_rect.width, _BAR_HEIGHT - 1),
        )
        font = ui_font(22)
        pygame.draw.rect(surface, (42, 48, 58), layout.population_button, border_radius=6)
        pygame.draw.rect(surface, (70, 76, 88), layout.population_button, width=1, border_radius=6)
        icon = population_icon()
        surface.blit(icon, layout.icon_rect.topleft)
        text_surf = font.render(layout.label, True, (228, 230, 238))
        surface.blit(text_surf, layout.label_pos)
        delivery_surf = font.render(layout.delivery_label, True, (205, 210, 220))
        surface.blit(delivery_surf, layout.delivery_pos)

        if layout.research_button is not None:
            pygame.draw.rect(surface, (42, 48, 58), layout.research_button, border_radius=6)
            pygame.draw.rect(surface, (70, 76, 88), layout.research_button, width=1, border_radius=6)
            research_surf = font.render(_research_button_label(), True, (228, 230, 238))
            surface.blit(
                research_surf,
                (
                    layout.research_button.centerx - research_surf.get_width() // 2,
                    layout.research_button.centery - research_surf.get_height() // 2,
                ),
            )

        # Temporary dev-only control: force asset cache reload.
        dev_asset_reload.draw_button(surface)
