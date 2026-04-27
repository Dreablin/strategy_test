"""Stone Mine panel extension with Active toggle and delivered counter."""

from __future__ import annotations

from dataclasses import dataclass

import pygame

from game.buildings.stone_mine import StoneMine
from game.resources import ResourceManager
from game.ui.building_panel import BuildingPanel

_PANEL_PAD = 16
_BTN_H = 32
_EXTRA_BOTTOM = 72


@dataclass(frozen=True, slots=True)
class StoneMinePanelLayout:
    frame: pygame.Rect
    close: pygame.Rect
    upgrade: pygame.Rect | None
    upgrade_enabled: bool
    demolish: pygame.Rect | None
    toggle: pygame.Rect


class StoneMinePanel:
    @staticmethod
    def supports_building(building) -> bool:
        return isinstance(building, StoneMine)

    @staticmethod
    def toggle_label(mine: StoneMine) -> str:
        return "Active" if mine.active else "Inactive"

    @staticmethod
    def delivered_line(mine: StoneMine) -> str:
        return f"Stones delivered: {mine.delivered_stone}"

    @staticmethod
    def storage_line(mine: StoneMine) -> str:
        return BuildingPanel.storage_line(mine)

    @staticmethod
    def layout(
        surface: pygame.Surface,
        mine: StoneMine,
        resources: ResourceManager,
        *,
        worker_assigned: bool,
    ) -> StoneMinePanelLayout:
        base = BuildingPanel.layout(
            surface,
            mine,
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
        return StoneMinePanelLayout(
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
        mine: StoneMine,
        resources: ResourceManager,
        *,
        worker_assigned: bool,
        worker_status: str = "empty",
        worker_working: bool = False,
    ) -> None:
        BuildingPanel.draw(
            surface,
            mine,
            resources,
            worker_assigned=worker_assigned,
            worker_status=worker_status,
            worker_working=worker_working,
            extra_bottom_px=_EXTRA_BOTTOM,
        )
        layout = StoneMinePanel.layout(surface, mine, resources, worker_assigned=worker_assigned)
        font = pygame.font.Font(None, 22)
        body = pygame.font.Font(None, 22)
        delivered = body.render(StoneMinePanel.delivered_line(mine), True, (200, 204, 214))
        storage = body.render(StoneMinePanel.storage_line(mine), True, (200, 204, 214))
        delivered_y = layout.toggle.top - 56
        storage_y = layout.toggle.top - 30
        surface.blit(delivered, (layout.frame.left + _PANEL_PAD, delivered_y))
        surface.blit(storage, (layout.frame.left + _PANEL_PAD, storage_y))

        active_bg = (84, 112, 84) if mine.active else (92, 64, 64)
        pygame.draw.rect(surface, active_bg, layout.toggle, border_radius=6)
        label = font.render(StoneMinePanel.toggle_label(mine), True, (240, 242, 250))
        surface.blit(
            label,
            (layout.toggle.centerx - label.get_width() // 2, layout.toggle.centery - label.get_height() // 2),
        )

    @staticmethod
    def click_action(
        surface: pygame.Surface,
        pos: tuple[int, int],
        mine: StoneMine,
        resources: ResourceManager,
        *,
        worker_assigned: bool,
    ) -> str | None:
        base_action = BuildingPanel.click_action(
            surface,
            pos,
            mine,
            resources,
            worker_assigned=worker_assigned,
            extra_bottom_px=_EXTRA_BOTTOM,
        )
        if base_action is not None:
            return base_action
        layout = StoneMinePanel.layout(surface, mine, resources, worker_assigned=worker_assigned)
        if layout.toggle.collidepoint(pos):
            return "toggle_active"
        return None
