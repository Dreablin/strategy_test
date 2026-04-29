"""Stone Mine panel extension with Active toggle."""

from __future__ import annotations

from dataclasses import dataclass

import pygame

from game.buildings.stone_mine import StoneMine
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
    def layout(
        surface: pygame.Surface,
        mine: StoneMine,
        *,
        worker_assigned: bool,
        production_status: str | None = None,
    ) -> StoneMinePanelLayout:
        base = BuildingPanel.layout(
            surface,
            mine,
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
        *,
        worker_assigned: bool,
        worker_status: str = "empty",
        production_status: str | None = None,
        worker_working: bool = False,
    ) -> None:
        BuildingPanel.draw(
            surface,
            mine,
            worker_assigned=worker_assigned,
            worker_status=worker_status,
            production_status=production_status,
            worker_working=worker_working,
            extra_bottom_px=_EXTRA_BOTTOM,
        )
        layout = StoneMinePanel.layout(
            surface,
            mine,
            worker_assigned=worker_assigned,
            production_status=production_status,
        )
        font = pygame.font.Font(None, 22)

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
        *,
        worker_assigned: bool,
        production_status: str | None = None,
    ) -> str | None:
        base_action = BuildingPanel.click_action(
            surface,
            pos,
            mine,
            worker_assigned=worker_assigned,
            production_status=production_status,
            extra_bottom_px=_EXTRA_BOTTOM,
        )
        if base_action is not None:
            return base_action
        layout = StoneMinePanel.layout(
            surface,
            mine,
            worker_assigned=worker_assigned,
            production_status=production_status,
        )
        if layout.toggle.collidepoint(pos):
            return "toggle_active"
        return None
