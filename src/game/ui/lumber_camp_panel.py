"""Lumber Camp panel extension with Active toggle and delivered counter."""

from __future__ import annotations

from dataclasses import dataclass

import pygame

from game.buildings.lumber_camp import LumberCamp
from game.resources import ResourceManager
from game.ui.building_panel import BuildingPanel

_PANEL_PAD = 16
_BTN_H = 32
_EXTRA_BOTTOM = 72


@dataclass(frozen=True, slots=True)
class LumberCampPanelLayout:
    frame: pygame.Rect
    close: pygame.Rect
    upgrade: pygame.Rect | None
    upgrade_enabled: bool
    demolish: pygame.Rect | None
    toggle: pygame.Rect


class LumberCampPanel:
    @staticmethod
    def supports_building(building) -> bool:
        return isinstance(building, LumberCamp)

    @staticmethod
    def toggle_label(camp: LumberCamp) -> str:
        return "Active" if camp.active else "Inactive"

    @staticmethod
    def delivered_line(camp: LumberCamp) -> str:
        return f"Wood delivered: {camp.delivered_wood}"

    @staticmethod
    def layout(
        surface: pygame.Surface,
        camp: LumberCamp,
        resources: ResourceManager,
        *,
        worker_assigned: bool,
    ) -> LumberCampPanelLayout:
        base = BuildingPanel.layout(
            surface,
            camp,
            resources,
            worker_assigned=worker_assigned,
            extra_bottom_px=_EXTRA_BOTTOM,
        )
        toggle = pygame.Rect(
            base.frame.left + _PANEL_PAD,
            base.frame.bottom - _PANEL_PAD - _BTN_H,
            base.frame.width - _PANEL_PAD * 2,
            _BTN_H,
        )
        return LumberCampPanelLayout(
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
        camp: LumberCamp,
        resources: ResourceManager,
        *,
        worker_assigned: bool,
        worker_status: str = "empty",
        worker_working: bool = False,
    ) -> None:
        BuildingPanel.draw(
            surface,
            camp,
            resources,
            worker_assigned=worker_assigned,
            worker_status=worker_status,
            worker_working=worker_working,
            extra_bottom_px=_EXTRA_BOTTOM,
        )
        layout = LumberCampPanel.layout(surface, camp, resources, worker_assigned=worker_assigned)
        font = pygame.font.Font(None, 22)
        body = pygame.font.Font(None, 22)
        delivered = body.render(LumberCampPanel.delivered_line(camp), True, (200, 204, 214))
        delivered_y = layout.toggle.top - 34
        surface.blit(delivered, (layout.frame.left + _PANEL_PAD, delivered_y))

        active_bg = (84, 112, 84) if camp.active else (92, 64, 64)
        pygame.draw.rect(surface, active_bg, layout.toggle, border_radius=6)
        label = font.render(LumberCampPanel.toggle_label(camp), True, (240, 242, 250))
        surface.blit(
            label,
            (layout.toggle.centerx - label.get_width() // 2, layout.toggle.centery - label.get_height() // 2),
        )

    @staticmethod
    def click_action(
        surface: pygame.Surface,
        pos: tuple[int, int],
        camp: LumberCamp,
        resources: ResourceManager,
        *,
        worker_assigned: bool,
    ) -> str | None:
        # Accept both default base panel hit targets (legacy tests) and expanded panel layout.
        base_action = BuildingPanel.click_action(
            surface,
            pos,
            camp,
            resources,
            worker_assigned=worker_assigned,
        )
        if base_action is not None:
            return base_action
        base_action = BuildingPanel.click_action(
            surface,
            pos,
            camp,
            resources,
            worker_assigned=worker_assigned,
            extra_bottom_px=_EXTRA_BOTTOM,
        )
        if base_action is not None:
            return base_action
        layout = LumberCampPanel.layout(surface, camp, resources, worker_assigned=worker_assigned)
        if layout.toggle.collidepoint(pos):
            return "toggle_active"
        return None
