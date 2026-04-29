"""Town Hall modal extension: no upgrade/demolish, no direct hiring."""

from __future__ import annotations

from dataclasses import dataclass

import pygame

from game.assets import resource_icon
from game.buildings.town_hall import TownHall
from game.ui.building_panel import BuildingPanel

_PANEL_PAD = 16
_BTN_H = 32
_GAP = 8
_EXTRA_BOTTOM = _BTN_H + _GAP
_STORAGE_GAP = 12
_STORAGE_PANEL_W = 300
_STORAGE_ROWS: tuple[tuple[str, str], ...] = (
    ("wood", "Wood"),
    ("boards", "Boards"),
    ("stone", "Stone"),
    ("iron", "Iron"),
    ("wheat", "Wheat"),
)


@dataclass(frozen=True, slots=True)
class TownHallPanelLayout:
    """Town Hall panel frame and hire button rects."""

    frame: pygame.Rect
    storage_frame: pygame.Rect
    close: pygame.Rect
    upgrade: pygame.Rect | None
    upgrade_enabled: bool
    hire_buttons: tuple[tuple[str, pygame.Rect], ...]
    hire_enabled: dict[str, bool]


class TownHallPanel:
    """Town Hall panel: base info rows + upgrade only."""

    @staticmethod
    def layout(
        surface: pygame.Surface, town_hall: TownHall, *, worker_assigned: bool
    ) -> TownHallPanelLayout:
        base = BuildingPanel.layout(
            surface,
            town_hall,
            worker_assigned=worker_assigned,
            show_upgrade=False,
            show_demolish=False,
            extra_bottom_px=_EXTRA_BOTTOM,
        )
        upgrade: pygame.Rect | None = None
        upgrade_enabled = False
        if town_hall.level < TownHall.max_level():
            upgrade_enabled = True
            upgrade = pygame.Rect(
                base.frame.left + _PANEL_PAD,
                base.frame.bottom - _PANEL_PAD - (_BTN_H + 8),
                base.frame.width - _PANEL_PAD * 2,
                _BTN_H,
            )

        return TownHallPanelLayout(
            frame=base.frame,
            storage_frame=pygame.Rect(
                base.frame.right + _STORAGE_GAP,
                base.frame.top,
                _STORAGE_PANEL_W,
                base.frame.height,
            ),
            close=base.close,
            upgrade=upgrade,
            upgrade_enabled=upgrade_enabled,
            hire_buttons=tuple(),
            hire_enabled={},
        )

    @staticmethod
    def draw(
        surface: pygame.Surface, town_hall: TownHall, *, worker_assigned: bool
    ) -> None:
        BuildingPanel.draw(
            surface,
            town_hall,
            worker_assigned=worker_assigned,
            show_upgrade=False,
            show_demolish=False,
            extra_bottom_px=_EXTRA_BOTTOM,
        )
        layout = TownHallPanel.layout(surface, town_hall, worker_assigned=worker_assigned)
        font = pygame.font.Font(None, 22)
        title_font = pygame.font.Font(None, 24)

        if layout.upgrade is not None:
            bg = (64, 110, 168) if layout.upgrade_enabled else (52, 56, 64)
            fg = (240, 242, 250) if layout.upgrade_enabled else (130, 134, 142)
            pygame.draw.rect(surface, bg, layout.upgrade, border_radius=6)
            text = font.render("Upgrade Town Hall — Free", True, fg)
            surface.blit(
                text,
                (layout.upgrade.centerx - text.get_width() // 2, layout.upgrade.centery - text.get_height() // 2),
            )

        # Secondary storage panel (warehouse overview).
        sf = layout.storage_frame
        pygame.draw.rect(surface, (36, 40, 52), sf, border_radius=10)
        pygame.draw.rect(surface, (72, 78, 92), sf, width=2, border_radius=10)
        title = title_font.render("Warehouse", True, (238, 240, 248))
        surface.blit(title, (sf.left + _PANEL_PAD, sf.top + _PANEL_PAD))
        cols = 4
        cell_gap = 8
        inner_w = sf.width - _PANEL_PAD * 2
        cell_w = max(1, (inner_w - cell_gap * (cols - 1)) // cols)
        cell_h = 72
        start_y = sf.top + _PANEL_PAD + 32
        for idx, (res_key, res_label) in enumerate(_STORAGE_ROWS):
            row = idx // cols
            col = idx % cols
            x = sf.left + _PANEL_PAD + col * (cell_w + cell_gap)
            y = start_y + row * (cell_h + cell_gap)
            cell = pygame.Rect(x, y, cell_w, cell_h)
            pygame.draw.rect(surface, (52, 56, 64), cell, border_radius=6)
            pygame.draw.rect(surface, (92, 98, 112), cell, width=1, border_radius=6)
            icon = pygame.transform.smoothscale(resource_icon(res_key), (20, 20))
            surface.blit(icon, (cell.left + 8, cell.top + 8))
            qty = int(town_hall.warehouse_amount(res_key))
            qty_s = font.render(str(qty), True, (236, 240, 246))
            surface.blit(qty_s, (cell.left + 34, cell.top + 10))
            label_s = pygame.font.Font(None, 18).render(res_label, True, (170, 176, 188))
            surface.blit(label_s, (cell.left + 8, cell.bottom - label_s.get_height() - 8))


    @staticmethod
    def click_action(
        surface: pygame.Surface,
        pos: tuple[int, int],
        town_hall: TownHall,
        *,
        worker_assigned: bool,
    ) -> str | None:
        """Return ``close`` or ``upgrade`` when active, else ``None``."""
        base_action = BuildingPanel.click_action(
            surface,
            pos,
            town_hall,
            worker_assigned=worker_assigned,
            show_upgrade=False,
            show_demolish=False,
            extra_bottom_px=_EXTRA_BOTTOM,
        )
        if base_action == "close":
            return "close"
        layout = TownHallPanel.layout(surface, town_hall, worker_assigned=worker_assigned)
        if layout.storage_frame.collidepoint(pos):
            return None
        if layout.upgrade is not None and layout.upgrade.collidepoint(pos):
            return "upgrade" if layout.upgrade_enabled else None
        return None
