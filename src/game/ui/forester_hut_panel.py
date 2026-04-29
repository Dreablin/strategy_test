"""Forester Hut panel extension with Active toggle."""

from __future__ import annotations

from dataclasses import dataclass

import pygame

from game.buildings.forester_hut import ForesterHut
from game.ui.building_panel import BuildingPanel

_PANEL_PAD = 16
_BTN_H = 32
_GAP = 8
_EXTRA_BOTTOM = 2 * _BTN_H + _GAP + _PANEL_PAD


@dataclass(frozen=True, slots=True)
class ForesterHutPanelLayout:
    frame: pygame.Rect
    close: pygame.Rect
    upgrade: pygame.Rect | None
    upgrade_enabled: bool
    demolish: pygame.Rect | None
    toggle: pygame.Rect


class ForesterHutPanel:
    @staticmethod
    def supports_building(building) -> bool:
        return isinstance(building, ForesterHut)

    @staticmethod
    def toggle_label(hut: ForesterHut) -> str:
        return "Active" if hut.active else "Inactive"

    @staticmethod
    def layout(
        surface: pygame.Surface,
        hut: ForesterHut,
        *,
        worker_assigned: bool,
        production_status: str | None = None,
    ) -> ForesterHutPanelLayout:
        base = BuildingPanel.layout(
            surface,
            hut,
            worker_assigned=worker_assigned,
            production_status=production_status,
            show_upgrade=False,
            show_demolish=False,
            extra_bottom_px=_EXTRA_BOTTOM,
        )
        demolish = pygame.Rect(
            base.frame.left + _PANEL_PAD,
            base.frame.bottom - _PANEL_PAD - (2 * _BTN_H + _GAP),
            base.frame.width - _PANEL_PAD * 2,
            _BTN_H,
        )
        toggle = pygame.Rect(
            base.frame.left + _PANEL_PAD,
            base.frame.bottom - _PANEL_PAD - _BTN_H,
            base.frame.width - _PANEL_PAD * 2,
            _BTN_H,
        )
        return ForesterHutPanelLayout(
            frame=base.frame,
            close=base.close,
            upgrade=base.upgrade,
            upgrade_enabled=base.upgrade_enabled,
            demolish=demolish,
            toggle=toggle,
        )

    @staticmethod
    def draw(
        surface: pygame.Surface,
        hut: ForesterHut,
        *,
        worker_assigned: bool,
        worker_status: str = "empty",
        production_status: str | None = None,
        worker_working: bool = False,
    ) -> None:
        BuildingPanel.draw(
            surface,
            hut,
            worker_assigned=worker_assigned,
            worker_status=worker_status,
            production_status=production_status,
            worker_working=worker_working,
            show_upgrade=False,
            show_demolish=False,
            extra_bottom_px=_EXTRA_BOTTOM,
        )
        layout = ForesterHutPanel.layout(
            surface,
            hut,
            worker_assigned=worker_assigned,
            production_status=production_status,
        )
        font = pygame.font.Font(None, 22)
        if layout.demolish is not None:
            pygame.draw.rect(surface, (140, 48, 52), layout.demolish, border_radius=6)
            label = font.render("Demolish", True, (255, 240, 240))
            surface.blit(
                label,
                (
                    layout.demolish.centerx - label.get_width() // 2,
                    layout.demolish.centery - label.get_height() // 2,
                ),
            )
        active_bg = (84, 112, 84) if hut.active else (92, 64, 64)
        pygame.draw.rect(surface, active_bg, layout.toggle, border_radius=6)
        label = font.render(ForesterHutPanel.toggle_label(hut), True, (240, 242, 250))
        surface.blit(
            label,
            (layout.toggle.centerx - label.get_width() // 2, layout.toggle.centery - label.get_height() // 2),
        )

    @staticmethod
    def click_action(
        surface: pygame.Surface,
        pos: tuple[int, int],
        hut: ForesterHut,
        *,
        worker_assigned: bool,
        production_status: str | None = None,
    ) -> str | None:
        base_action = BuildingPanel.click_action(
            surface,
            pos,
            hut,
            worker_assigned=worker_assigned,
            production_status=production_status,
            show_upgrade=False,
            show_demolish=False,
            extra_bottom_px=_EXTRA_BOTTOM,
        )
        if base_action is not None:
            return base_action
        layout = ForesterHutPanel.layout(
            surface,
            hut,
            worker_assigned=worker_assigned,
            production_status=production_status,
        )
        if layout.demolish is not None and layout.demolish.collidepoint(pos):
            return "demolish"
        if layout.toggle.collidepoint(pos):
            return "toggle_active"
        return None
