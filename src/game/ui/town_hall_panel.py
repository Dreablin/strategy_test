"""Town Hall modal extension: no upgrade/demolish, no direct hiring."""

from __future__ import annotations

from dataclasses import dataclass

import pygame

from game.buildings.costs import upgrade_cost
from game.buildings.town_hall import TownHall
from game.resources import ResourceManager
from game.ui.building_panel import BuildingPanel

_PANEL_PAD = 16
_BTN_H = 32
_GAP = 8
_EXTRA_BOTTOM = _BTN_H + _GAP


@dataclass(frozen=True, slots=True)
class TownHallPanelLayout:
    """Town Hall panel frame and hire button rects."""

    frame: pygame.Rect
    close: pygame.Rect
    upgrade: pygame.Rect | None
    upgrade_enabled: bool
    hire_buttons: tuple[tuple[str, pygame.Rect], ...]
    hire_enabled: dict[str, bool]


class TownHallPanel:
    @staticmethod
    def _format_cost(cost: dict[str, int]) -> str:
        parts: list[str] = []
        for key in ("wood", "stone", "iron", "food"):
            value = int(cost.get(key, 0))
            if value > 0:
                parts.append(f"{value} {key}")
        return ", ".join(parts) if parts else "—"

    """Town Hall panel: base info rows + upgrade only."""

    @staticmethod
    def layout(
        surface: pygame.Surface, town_hall: TownHall, resources: ResourceManager, *, worker_assigned: bool
    ) -> TownHallPanelLayout:
        base = BuildingPanel.layout(
            surface,
            town_hall,
            resources,
            worker_assigned=worker_assigned,
            show_upgrade=False,
            show_demolish=False,
            extra_bottom_px=_EXTRA_BOTTOM,
        )
        upgrade: pygame.Rect | None = None
        upgrade_enabled = False
        if town_hall.level < TownHall.max_level():
            try:
                up_cost = upgrade_cost(town_hall.level)
            except ValueError:
                up_cost = {}
            else:
                upgrade_enabled = resources.has(up_cost)
            upgrade = pygame.Rect(
                base.frame.left + _PANEL_PAD,
                base.frame.bottom - _PANEL_PAD - (_BTN_H + 8),
                base.frame.width - _PANEL_PAD * 2,
                _BTN_H,
            )

        return TownHallPanelLayout(
            frame=base.frame,
            close=base.close,
            upgrade=upgrade,
            upgrade_enabled=upgrade_enabled,
            hire_buttons=tuple(),
            hire_enabled={},
        )

    @staticmethod
    def draw(
        surface: pygame.Surface, town_hall: TownHall, resources: ResourceManager, *, worker_assigned: bool
    ) -> None:
        BuildingPanel.draw(
            surface,
            town_hall,
            resources,
            worker_assigned=worker_assigned,
            show_upgrade=False,
            show_demolish=False,
            extra_bottom_px=_EXTRA_BOTTOM,
        )
        layout = TownHallPanel.layout(surface, town_hall, resources, worker_assigned=worker_assigned)
        font = pygame.font.Font(None, 22)

        if layout.upgrade is not None:
            bg = (64, 110, 168) if layout.upgrade_enabled else (52, 56, 64)
            fg = (240, 242, 250) if layout.upgrade_enabled else (130, 134, 142)
            pygame.draw.rect(surface, bg, layout.upgrade, border_radius=6)
            cost = upgrade_cost(town_hall.level)
            text = font.render(f"Upgrade Town Hall — {TownHallPanel._format_cost(cost)}", True, fg)
            surface.blit(
                text,
                (layout.upgrade.centerx - text.get_width() // 2, layout.upgrade.centery - text.get_height() // 2),
            )


    @staticmethod
    def click_action(
        surface: pygame.Surface,
        pos: tuple[int, int],
        town_hall: TownHall,
        resources: ResourceManager,
        *,
        worker_assigned: bool,
    ) -> str | None:
        """Return ``close`` or ``upgrade`` when active, else ``None``."""
        base_action = BuildingPanel.click_action(
            surface,
            pos,
            town_hall,
            resources,
            worker_assigned=worker_assigned,
            show_upgrade=False,
            show_demolish=False,
            extra_bottom_px=_EXTRA_BOTTOM,
        )
        if base_action == "close":
            return "close"
        layout = TownHallPanel.layout(surface, town_hall, resources, worker_assigned=worker_assigned)
        if layout.upgrade is not None and layout.upgrade.collidepoint(pos):
            return "upgrade" if layout.upgrade_enabled else None
        return None
