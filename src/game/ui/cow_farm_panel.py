"""Cow farm panel: shared building chrome, local storage rows, active toggle (progress in T302)."""

from __future__ import annotations

from dataclasses import dataclass

import pygame

from game.buildings.cow_farm import CowFarm
from game.ui.building_panel import BuildingPanel

_PANEL_PAD = 16
_BTN_H = 32
_STORAGE_LINE_SP = 22
# Reserve lower panel height like chicken farm so storage rows sit above upgrade/demolish.
_EXTRA_BOTTOM = 152
# First storage line Y: same anchor as chicken farm details (between worker row and action buttons).
_STORAGE_BLOCK_TOP_OFF = _PANEL_PAD + 4 * 26 + 32


@dataclass(frozen=True, slots=True)
class CowFarmPanelLayout:
    frame: pygame.Rect
    close: pygame.Rect
    upgrade: pygame.Rect | None
    upgrade_enabled: bool
    demolish: pygame.Rect | None
    toggle: pygame.Rect


class CowFarmPanel:
    @staticmethod
    def supports_building(building: object) -> bool:
        return isinstance(building, CowFarm)

    @staticmethod
    def storage_line_texts(farm: CowFarm) -> tuple[str, str, str, str]:
        return (
            f"Input wheat: {farm.wheat_amount()} / {farm.wheat_capacity()}",
            f"Input water: {farm.water_amount()} / {farm.water_capacity()}",
            f"Output beef: {farm.beef_amount()} / {farm.beef_capacity()}",
            f"Output hide: {farm.hide_amount()} / {farm.hide_capacity()}",
        )

    @staticmethod
    def storage_block_top(frame_top: int) -> int:
        return frame_top + _STORAGE_BLOCK_TOP_OFF

    @staticmethod
    def toggle_label(farm: CowFarm) -> str:
        return "Active" if farm.active else "Inactive"

    @staticmethod
    def layout(
        surface: pygame.Surface,
        farm: CowFarm,
        *,
        worker_assigned: bool,
        production_status: str | None = None,
    ) -> CowFarmPanelLayout:
        base = BuildingPanel.layout(
            surface,
            farm,
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
        return CowFarmPanelLayout(
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
        farm: CowFarm,
        *,
        worker_assigned: bool,
        worker_status: str = "empty",
        production_status: str | None = None,
        now_ms: int,
    ) -> None:
        _ = now_ms
        BuildingPanel.draw(
            surface,
            farm,
            worker_assigned=worker_assigned,
            worker_status=worker_status,
            production_status=production_status,
            worker_working=worker_status == "assigned",
            extra_bottom_px=_EXTRA_BOTTOM,
        )
        layout = CowFarmPanel.layout(
            surface,
            farm,
            worker_assigned=worker_assigned,
            production_status=production_status,
        )
        font = pygame.font.Font(None, 22)
        body = pygame.font.Font(None, 20)
        sy = CowFarmPanel.storage_block_top(layout.frame.top)
        for i, line in enumerate(CowFarmPanel.storage_line_texts(farm)):
            surf = body.render(line, True, (200, 204, 214))
            surface.blit(surf, (layout.frame.left + _PANEL_PAD, sy + i * _STORAGE_LINE_SP))
        active_bg = (84, 112, 84) if farm.active else (92, 64, 64)
        pygame.draw.rect(surface, active_bg, layout.toggle, border_radius=6)
        label = font.render(CowFarmPanel.toggle_label(farm), True, (240, 242, 250))
        surface.blit(
            label,
            (layout.toggle.centerx - label.get_width() // 2, layout.toggle.centery - label.get_height() // 2),
        )

    @staticmethod
    def click_action(
        surface: pygame.Surface,
        pos: tuple[int, int],
        farm: CowFarm,
        *,
        worker_assigned: bool,
        production_status: str | None = None,
    ) -> str | None:
        base_action = BuildingPanel.click_action(
            surface,
            pos,
            farm,
            worker_assigned=worker_assigned,
            production_status=production_status,
            extra_bottom_px=_EXTRA_BOTTOM,
        )
        if base_action is not None:
            return base_action
        layout = CowFarmPanel.layout(
            surface,
            farm,
            worker_assigned=worker_assigned,
            production_status=production_status,
        )
        if layout.toggle.collidepoint(pos):
            return "toggle_active"
        return None
