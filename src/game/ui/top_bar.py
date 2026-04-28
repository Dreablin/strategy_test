"""Fixed-height top HUD strip for population totals."""

from __future__ import annotations

from dataclasses import dataclass

import pygame

from game import dev_asset_reload

_BAR_HEIGHT = 48


def _population_icon(size: int = 24) -> pygame.Surface:
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx = size // 2
    pygame.draw.circle(surf, (218, 206, 120), (cx, cx - 4), max(3, size // 6))
    pygame.draw.circle(surf, (160, 148, 76), (cx, cx + 7), max(5, size // 4))
    pygame.draw.circle(surf, (34, 34, 40), (cx, cx - 4), max(3, size // 6), 1)
    pygame.draw.circle(surf, (34, 34, 40), (cx, cx + 7), max(5, size // 4), 1)
    return surf


@dataclass(frozen=True, slots=True)
class TopBarLayout:
    bar_rect: pygame.Rect
    icon_rect: pygame.Rect
    label: str
    label_pos: tuple[int, int]


class TopBar:
    """48 px strip: `[population icon] current (max N)`."""

    @staticmethod
    def layout(surface: pygame.Surface, *, current_population: int, max_population: int) -> TopBarLayout:
        width = surface.get_width()
        bar_rect = pygame.Rect(0, 0, width, _BAR_HEIGHT)
        icon = _population_icon()
        icon_x = 10
        icon_y = (_BAR_HEIGHT - icon.get_height()) // 2
        icon_rect = pygame.Rect(icon_x, icon_y, icon.get_width(), icon.get_height())
        label = f"{current_population} (max {max_population})"
        label_pos = (icon_rect.right + 8, (_BAR_HEIGHT - 22) // 2)
        return TopBarLayout(
            bar_rect=bar_rect,
            icon_rect=icon_rect,
            label=label,
            label_pos=label_pos,
        )

    @staticmethod
    def draw(surface: pygame.Surface, *, current_population: int, max_population: int) -> None:
        layout = TopBar.layout(
            surface,
            current_population=current_population,
            max_population=max_population,
        )
        pygame.draw.rect(surface, (32, 36, 44), layout.bar_rect)
        pygame.draw.line(
            surface,
            (56, 60, 68),
            (0, _BAR_HEIGHT - 1),
            (layout.bar_rect.width, _BAR_HEIGHT - 1),
        )
        font = pygame.font.Font(None, 22)
        icon = _population_icon()
        surface.blit(icon, layout.icon_rect.topleft)
        text_surf = font.render(layout.label, True, (228, 230, 238))
        surface.blit(text_surf, layout.label_pos)

        # Temporary dev-only control: force asset cache reload.
        dev_asset_reload.draw_button(surface)
