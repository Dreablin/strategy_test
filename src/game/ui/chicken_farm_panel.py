"""Chicken farm panel with active toggle and production details."""

from __future__ import annotations

from dataclasses import dataclass

import pygame

from game.buildings.chicken_farm import ChickenFarm
from game.ui.building_panel import BuildingPanel

_PANEL_PAD = 16
_BTN_H = 32
_EXTRA_BOTTOM = 152


@dataclass(frozen=True, slots=True)
class ChickenFarmPanelLayout:
    frame: pygame.Rect
    close: pygame.Rect
    upgrade: pygame.Rect | None
    upgrade_enabled: bool
    demolish: pygame.Rect | None
    toggle: pygame.Rect


class ChickenFarmPanel:
    @staticmethod
    def supports_building(building) -> bool:
        return isinstance(building, ChickenFarm)

    @staticmethod
    def toggle_label(farm: ChickenFarm) -> str:
        return "Active" if farm.active else "Inactive"

    @staticmethod
    def blocked_reason(
        farm: ChickenFarm,
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
        if farm.output_amount() >= farm.output_capacity():
            return "output full"
        if farm.input_amount() <= 0:
            return "no grain"
        if farm.water_amount() <= 0:
            return "no water"
        return "running"

    @staticmethod
    def layout(
        surface: pygame.Surface,
        farm: ChickenFarm,
        *,
        worker_assigned: bool,
        production_status: str | None = None,
    ) -> ChickenFarmPanelLayout:
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
        return ChickenFarmPanelLayout(
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
        farm: ChickenFarm,
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
        layout = ChickenFarmPanel.layout(
            surface,
            farm,
            worker_assigned=worker_assigned,
            production_status=production_status,
        )
        font = pygame.font.Font(None, 22)
        body = pygame.font.Font(None, 20)

        details_y = layout.frame.top + _PANEL_PAD + 4 * 26 + 32
        grain = body.render(
            f"Input grain: {farm.input_amount()} / {farm.input_capacity()}",
            True,
            (200, 204, 214),
        )
        surface.blit(grain, (layout.frame.left + _PANEL_PAD, details_y))
        water = body.render(
            f"Input water: {farm.water_amount()} / {farm.water_capacity()}",
            True,
            (200, 204, 214),
        )
        surface.blit(water, (layout.frame.left + _PANEL_PAD, details_y + 22))
        chicken = body.render(
            f"Output chicken: {farm.output_amount()} / {farm.output_capacity()}",
            True,
            (200, 204, 214),
        )
        surface.blit(chicken, (layout.frame.left + _PANEL_PAD, details_y + 44))
        reason = ChickenFarmPanel.blocked_reason(
            farm,
            worker_status=worker_status,
            production_status=production_status,
        )
        reason_text = body.render(f"Blocked: {reason}", True, (200, 204, 214))
        surface.blit(reason_text, (layout.frame.left + _PANEL_PAD, details_y + 66))

        bar_y = details_y + 90
        bar_bg = pygame.Rect(layout.frame.left + _PANEL_PAD, bar_y, layout.frame.width - _PANEL_PAD * 2, 12)
        pygame.draw.rect(surface, (52, 58, 66), bar_bg, border_radius=4)
        progress = max(0.0, min(1.0, farm.processing_progress(now_ms)))
        if progress > 0.0:
            fill = pygame.Rect(bar_bg.left, bar_bg.top, max(1, int(round(bar_bg.width * progress))), bar_bg.height)
            pygame.draw.rect(surface, (214, 198, 154), fill, border_radius=4)
        pygame.draw.rect(surface, (116, 124, 136), bar_bg, width=1, border_radius=4)

        active_bg = (84, 112, 84) if farm.active else (92, 64, 64)
        pygame.draw.rect(surface, active_bg, layout.toggle, border_radius=6)
        label = font.render(ChickenFarmPanel.toggle_label(farm), True, (240, 242, 250))
        surface.blit(label, (layout.toggle.centerx - label.get_width() // 2, layout.toggle.centery - label.get_height() // 2))

    @staticmethod
    def click_action(
        surface: pygame.Surface,
        pos: tuple[int, int],
        farm: ChickenFarm,
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
        layout = ChickenFarmPanel.layout(
            surface,
            farm,
            worker_assigned=worker_assigned,
            production_status=production_status,
        )
        if layout.toggle.collidepoint(pos):
            return "toggle_active"
        return None
