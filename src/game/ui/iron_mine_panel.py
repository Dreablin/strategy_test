"""Iron Mine panel with local storage and mining progress."""

from __future__ import annotations

from dataclasses import dataclass

import pygame

from game.buildings.iron_mine import IronMine
from game.ui.building_panel import BuildingPanel
from game.ui.panel_i18n import blocked_line
from game.ui.fonts import ui_font

_PANEL_PAD = 16
_EXTRA_BOTTOM = 72


@dataclass(frozen=True, slots=True)
class IronMinePanelLayout:
    frame: pygame.Rect
    close: pygame.Rect
    upgrade: pygame.Rect | None
    upgrade_enabled: bool
    demolish: pygame.Rect | None


class IronMinePanel:
    @staticmethod
    def supports_building(building) -> bool:
        return isinstance(building, IronMine)

    @staticmethod
    def blocked_reason(mine: IronMine, *, production_status: str | None) -> str:
        status = (production_status or "").strip()
        if status == "no_worker":
            return "no worker"
        if status == "resting":
            return "resting"
        if status == "mining":
            return "running"
        if mine.is_storage_full():
            return "storage full"
        return "running"

    @staticmethod
    def layout(
        surface: pygame.Surface,
        mine: IronMine,
        *,
        worker_assigned: bool,
        production_status: str | None = None,
    ) -> IronMinePanelLayout:
        base = BuildingPanel.layout(
            surface,
            mine,
            worker_assigned=worker_assigned,
            production_status=production_status,
            extra_bottom_px=_EXTRA_BOTTOM,
        )
        return IronMinePanelLayout(
            frame=base.frame,
            close=base.close,
            upgrade=base.upgrade,
            upgrade_enabled=base.upgrade_enabled,
            demolish=base.demolish,
        )

    @staticmethod
    def draw(
        surface: pygame.Surface,
        mine: IronMine,
        *,
        worker_assigned: bool,
        worker_status: str = "empty",
        production_status: str | None = None,
        now_ms: int,
    ) -> None:
        BuildingPanel.draw(
            surface,
            mine,
            worker_assigned=worker_assigned,
            worker_status=worker_status,
            production_status=production_status,
            worker_working=worker_status == "assigned",
            extra_bottom_px=_EXTRA_BOTTOM,
        )
        layout = IronMinePanel.layout(
            surface,
            mine,
            worker_assigned=worker_assigned,
            production_status=production_status,
        )
        body = ui_font(20)

        details_y = layout.frame.top + _PANEL_PAD + 4 * 26 + 32
        reason = IronMinePanel.blocked_reason(mine, production_status=production_status)
        reason_text = body.render(blocked_line(reason), True, (200, 204, 214))
        surface.blit(reason_text, (layout.frame.left + _PANEL_PAD, details_y))

        bar_y = details_y + 26
        bar_bg = pygame.Rect(layout.frame.left + _PANEL_PAD, bar_y, layout.frame.width - _PANEL_PAD * 2, 12)
        pygame.draw.rect(surface, (52, 58, 66), bar_bg, border_radius=4)
        progress = max(0.0, min(1.0, mine.mining_progress(now_ms)))
        if progress > 0.0:
            fill = pygame.Rect(bar_bg.left, bar_bg.top, max(1, int(round(bar_bg.width * progress))), bar_bg.height)
            pygame.draw.rect(surface, (196, 116, 92), fill, border_radius=4)
        pygame.draw.rect(surface, (116, 124, 136), bar_bg, width=1, border_radius=4)

    @staticmethod
    def click_action(
        surface: pygame.Surface,
        pos: tuple[int, int],
        mine: IronMine,
        *,
        worker_assigned: bool,
        production_status: str | None = None,
    ) -> str | None:
        return BuildingPanel.click_action(
            surface,
            pos,
            mine,
            worker_assigned=worker_assigned,
            production_status=production_status,
            extra_bottom_px=_EXTRA_BOTTOM,
        )
