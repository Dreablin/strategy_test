"""Cow farm panel: storage rows, blocked hint, progress bar, and active toggle."""

from __future__ import annotations

from dataclasses import dataclass

import pygame

from game.buildings.cow_farm import CowFarm
from game.ui.building_panel import BuildingPanel
from game.ui.fonts import ui_font

_PANEL_PAD = 16
_BTN_H = 32
_STORAGE_LINE_SP = 22
_BAR_H = 12
_BLOCKED_TO_BAR_GAP = 24
# Chicken-style detail stack plus one extra storage row (four inputs/outputs vs three).
_EXTRA_BOTTOM = 152 + _STORAGE_LINE_SP
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
    def blocked_reason(
        farm: CowFarm,
        *,
        worker_status: str,
        production_status: str | None,
    ) -> str:
        status = (production_status or "").strip().lower()
        if not farm.active:
            return "inactive"
        if worker_status == "empty" or status == "no worker":
            return "no worker"
        if status == "resting":
            return "resting"
        if not farm.has_recipe_output_space():
            return "output full"
        if farm.wheat_amount() < farm.recipe_wheat_required():
            return "no wheat"
        if farm.water_amount() < farm.recipe_water_required():
            return "no water"
        return "running"

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
        font = ui_font(22)
        body = ui_font(20)
        sy = CowFarmPanel.storage_block_top(layout.frame.top)
        for i, line in enumerate(CowFarmPanel.storage_line_texts(farm)):
            surf = body.render(line, True, (200, 204, 214))
            surface.blit(surf, (layout.frame.left + _PANEL_PAD, sy + i * _STORAGE_LINE_SP))
        blocked_y = sy + 4 * _STORAGE_LINE_SP
        reason = CowFarmPanel.blocked_reason(
            farm,
            worker_status=worker_status,
            production_status=production_status,
        )
        reason_surf = body.render(f"Blocked: {reason}", True, (200, 204, 214))
        surface.blit(reason_surf, (layout.frame.left + _PANEL_PAD, blocked_y))
        bar_y = blocked_y + _BLOCKED_TO_BAR_GAP
        bar_bg = pygame.Rect(layout.frame.left + _PANEL_PAD, bar_y, layout.frame.width - _PANEL_PAD * 2, _BAR_H)
        pygame.draw.rect(surface, (52, 58, 66), bar_bg, border_radius=4)
        progress = max(0.0, min(1.0, farm.processing_progress(now_ms)))
        if progress > 0.0:
            fill_w = max(1, int(round(bar_bg.width * progress)))
            fill = pygame.Rect(bar_bg.left, bar_bg.top, fill_w, bar_bg.height)
            pygame.draw.rect(surface, (214, 198, 154), fill, border_radius=4)
        pygame.draw.rect(surface, (116, 124, 136), bar_bg, width=1, border_radius=4)
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
