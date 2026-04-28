"""Forester Hut panel extension with Active toggle."""

from __future__ import annotations

from dataclasses import dataclass

import pygame

from game.buildings.forester_hut import ForesterHut
from game.resources import ResourceManager
from game.ui.building_panel import BuildingPanel

_PANEL_PAD = 16
_BTN_H = 32
_EXTRA_BOTTOM = 72


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
        resources: ResourceManager,
        *,
        worker_assigned: bool,
        production_status: str | None = None,
    ) -> ForesterHutPanelLayout:
        base = BuildingPanel.layout(
            surface,
            hut,
            resources,
            worker_assigned=worker_assigned,
            production_status=production_status,
            extra_bottom_px=_EXTRA_BOTTOM,
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
            demolish=base.demolish,
            toggle=toggle,
        )

    @staticmethod
    def draw(
        surface: pygame.Surface,
        hut: ForesterHut,
        resources: ResourceManager,
        *,
        worker_assigned: bool,
        worker_status: str = "empty",
        production_status: str | None = None,
        worker_working: bool = False,
    ) -> None:
        BuildingPanel.draw(
            surface,
            hut,
            resources,
            worker_assigned=worker_assigned,
            worker_status=worker_status,
            production_status=production_status,
            worker_working=worker_working,
            extra_bottom_px=_EXTRA_BOTTOM,
        )
        layout = ForesterHutPanel.layout(
            surface,
            hut,
            resources,
            worker_assigned=worker_assigned,
            production_status=production_status,
        )
        font = pygame.font.Font(None, 22)
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
        resources: ResourceManager,
        *,
        worker_assigned: bool,
        production_status: str | None = None,
    ) -> str | None:
        base_action = BuildingPanel.click_action(
            surface,
            pos,
            hut,
            resources,
            worker_assigned=worker_assigned,
            production_status=production_status,
            extra_bottom_px=_EXTRA_BOTTOM,
        )
        if base_action is not None:
            return base_action
        layout = ForesterHutPanel.layout(
            surface,
            hut,
            resources,
            worker_assigned=worker_assigned,
            production_status=production_status,
        )
        if layout.toggle.collidepoint(pos):
            return "toggle_active"
        return None
