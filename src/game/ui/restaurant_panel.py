"""Restaurant panel with title, worker status, close, upgrade, demolish, active toggle."""

from __future__ import annotations

from dataclasses import dataclass

import pygame

from game.buildings.restaurant import Restaurant
from game.ui.building_panel import BuildingPanel


_PANEL_PAD = 16
_BTN_H = 32
_EXTRA_BOTTOM = _BTN_H + 8


@dataclass(frozen=True, slots=True)
class RestaurantPanelLayout:
    frame: pygame.Rect
    close: pygame.Rect
    upgrade: pygame.Rect | None
    upgrade_enabled: bool
    demolish: pygame.Rect | None
    toggle: pygame.Rect


class RestaurantPanel:
    @staticmethod
    def supports_building(building) -> bool:
        return isinstance(building, Restaurant)

    @staticmethod
    def toggle_label(restaurant: Restaurant) -> str:
        return "Active" if restaurant.active else "Inactive"

    @staticmethod
    def layout(
        surface: pygame.Surface,
        restaurant: Restaurant,
        *,
        worker_assigned: bool,
    ) -> RestaurantPanelLayout:
        base = BuildingPanel.layout(surface, restaurant, worker_assigned=worker_assigned, extra_bottom_px=_EXTRA_BOTTOM)
        toggle_rect = pygame.Rect(
            base.frame.left + _PANEL_PAD,
            base.frame.bottom - _PANEL_PAD - _BTN_H,
            base.frame.width - 2 * _PANEL_PAD,
            _BTN_H,
        )
        return RestaurantPanelLayout(
            frame=base.frame,
            close=base.close,
            upgrade=base.upgrade,
            upgrade_enabled=base.upgrade_enabled,
            demolish=base.demolish,
            toggle=toggle_rect,
        )

    @staticmethod
    def draw(
        surface: pygame.Surface,
        restaurant: Restaurant,
        *,
        worker_assigned: bool,
        now_ms: int = 0,
    ) -> RestaurantPanelLayout:
        lay = RestaurantPanel.layout(surface, restaurant, worker_assigned=worker_assigned)
        BuildingPanel.draw(surface, restaurant, worker_assigned=worker_assigned, extra_bottom_px=_EXTRA_BOTTOM)
        font = pygame.font.SysFont(None, 20)
        label = RestaurantPanel.toggle_label(restaurant)
        color = (80, 180, 80) if restaurant.active else (180, 80, 80)
        pygame.draw.rect(surface, color, lay.toggle, border_radius=4)
        text = font.render(label, True, (255, 255, 255))
        surface.blit(text, (lay.toggle.centerx - text.get_width() // 2, lay.toggle.centery - text.get_height() // 2))
        return lay

    @staticmethod
    def click_action(
        pos: tuple[int, int],
        layout: RestaurantPanelLayout,
    ) -> str | None:
        x, y = pos
        if layout.close.collidepoint(x, y):
            return "close"
        if layout.upgrade is not None and layout.upgrade.collidepoint(x, y):
            return "upgrade"
        if layout.demolish is not None and layout.demolish.collidepoint(x, y):
            return "demolish"
        if layout.toggle.collidepoint(x, y):
            return "toggle_active"
        return None
