"""Centered modal panel: building info, upgrade/demolish actions, close control."""

from __future__ import annotations

from dataclasses import dataclass

import pygame

from game.buildings.base import Building
from game.buildings.costs import upgrade_cost
from game.config import TICK_MS
from game.resources import ResourceManager

_PANEL_W = 420
_PANEL_PAD = 16
_ROW = 26
_BTN_H = 36
_CLOSE = 28

_DISPLAY_NAME: dict[str, str] = {
    "TOWN_HALL": "Town Hall",
    "LUMBER_CAMP": "Lumber Camp",
    "STONE_MINE": "Stone Mine",
    "IRON_MINE": "Iron Mine",
    "FARM": "Farm",
}

_DESCRIPTION: dict[str, str] = {
    "TOWN_HALL": "The heart of your settlement.",
    "LUMBER_CAMP": "Lumberjack chops trees for wood.",
    "STONE_MINE": "Stonecutter quarries stone.",
    "IRON_MINE": "Miner digs for iron.",
    "FARM": "Farmer grows food.",
}

_RESOURCE_LABEL: dict[str, str] = {
    "food": "food",
    "wood": "wood",
    "stone": "stone",
    "iron": "iron",
}


def _format_cost(cost: dict[str, int]) -> str:
    parts: list[str] = []
    for key in ("wood", "stone", "iron", "food"):
        if key in cost and cost[key]:
            parts.append(f"{cost[key]} {_RESOURCE_LABEL.get(key, key)}")
    return ", ".join(parts) if parts else ""


def _income_line(building: Building, *, worker_working: bool) -> str:
    inc = type(building).income(building.level)
    if not inc:
        return "Income: —"
    (res, n), = inc.items()
    if not worker_working:
        n = 0
    sec = TICK_MS // 1000
    return f"Income: +{n} {res} / {sec} s"


def _upgrade_label(building: Building) -> str:
    nxt = building.level + 1
    cost = upgrade_cost(building.type_tag, building.level)
    cost_s = _format_cost(cost)
    return f"Upgrade to Lv {nxt} — {cost_s}"


@dataclass(frozen=True, slots=True)
class BuildingPanelLayout:
    """Hit targets and outer frame for the modal (shared by draw and click handling)."""

    frame: pygame.Rect
    close: pygame.Rect
    upgrade: pygame.Rect | None
    upgrade_enabled: bool
    demolish: pygame.Rect | None


class BuildingPanel:
    """PRD §3 F-UI-PANEL-02: name, level, description, income, worker row, actions, ×."""

    @staticmethod
    def layout(
        surface: pygame.Surface,
        building: Building,
        resources: ResourceManager,
        *,
        worker_assigned: bool,
        show_upgrade: bool | None = None,
        show_demolish: bool = True,
        extra_bottom_px: int = 0,
    ) -> BuildingPanelLayout:
        sw, sh = surface.get_size()
        cls = type(building)
        max_lv = cls.max_level()
        if show_upgrade is None:
            show_upgrade = building.level < max_lv
        can_upgrade = bool(show_upgrade and building.level < max_lv)
        upgrade_enabled = False
        if can_upgrade and building.level < max_lv:
            try:
                cost = upgrade_cost(building.type_tag, building.level)
            except ValueError:
                can_upgrade = False
                cost = {}
            else:
                upgrade_enabled = resources.has(cost)

        text_rows = 5 + (1 if hasattr(building, "storage_capacity") and hasattr(building, "stored") else 0)
        btn_count = int(can_upgrade) + int(show_demolish)
        h = (
            _PANEL_PAD * 2
            + _ROW
            + text_rows * _ROW
            + (8 if btn_count else 0)
            + btn_count * (_BTN_H + 8)
            + 8
            + max(0, int(extra_bottom_px))
        )
        frame = pygame.Rect(sw // 2 - _PANEL_W // 2, sh // 2 - h // 2, _PANEL_W, h)
        close = pygame.Rect(
            frame.right - _PANEL_PAD - _CLOSE,
            frame.top + _PANEL_PAD,
            _CLOSE,
            _CLOSE,
        )

        y = frame.bottom - _PANEL_PAD - (btn_count * (_BTN_H + 8) if btn_count else 0)
        demolish_r: pygame.Rect | None = None
        upgrade_r: pygame.Rect | None = None
        if show_demolish:
            demolish_r = pygame.Rect(
                frame.left + _PANEL_PAD,
                y,
                frame.width - _PANEL_PAD * 2,
                _BTN_H,
            )
            y -= _BTN_H + 8
        if can_upgrade:
            upgrade_r = pygame.Rect(
                frame.left + _PANEL_PAD,
                y,
                frame.width - _PANEL_PAD * 2,
                _BTN_H,
            )

        return BuildingPanelLayout(
            frame=frame,
            close=close,
            upgrade=upgrade_r,
            upgrade_enabled=upgrade_enabled,
            demolish=demolish_r,
        )

    @staticmethod
    def draw(
        surface: pygame.Surface,
        building: Building,
        resources: ResourceManager,
        *,
        worker_assigned: bool,
        worker_status: str = "empty",
        worker_working: bool = False,
        show_upgrade: bool | None = None,
        show_demolish: bool = True,
        extra_bottom_px: int = 0,
    ) -> None:
        layout = BuildingPanel.layout(
            surface,
            building,
            resources,
            worker_assigned=worker_assigned,
            show_upgrade=show_upgrade,
            show_demolish=show_demolish,
            extra_bottom_px=extra_bottom_px,
        )
        dim = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        dim.fill((10, 12, 16, 170))
        surface.blit(dim, (0, 0))

        pygame.draw.rect(surface, (36, 40, 52), layout.frame, border_radius=10)
        pygame.draw.rect(surface, (72, 78, 92), layout.frame, width=2, border_radius=10)

        title_font = pygame.font.Font(None, 28)
        body_font = pygame.font.Font(None, 22)
        btn_font = pygame.font.Font(None, 22)

        name = _DISPLAY_NAME.get(building.type_tag, building.type_tag)
        title = title_font.render(f"{name} — Lv {building.level}", True, (238, 240, 248))
        surface.blit(title, (layout.frame.left + _PANEL_PAD, layout.frame.top + _PANEL_PAD))

        pygame.draw.line(
            surface,
            (200, 82, 82),
            (layout.close.left + 6, layout.close.top + 6),
            (layout.close.right - 7, layout.close.bottom - 7),
            2,
        )
        pygame.draw.line(
            surface,
            (200, 82, 82),
            (layout.close.right - 7, layout.close.top + 6),
            (layout.close.left + 6, layout.close.bottom - 7),
            2,
        )

        y = layout.frame.top + _PANEL_PAD + _ROW + 6
        desc = _DESCRIPTION.get(building.type_tag, "")
        surface.blit(body_font.render(desc, True, (200, 204, 214)), (layout.frame.left + _PANEL_PAD, y))
        y += _ROW
        surface.blit(
            body_font.render(_income_line(building, worker_working=worker_working), True, (200, 204, 214)),
            (layout.frame.left + _PANEL_PAD, y),
        )
        y += _ROW
        if worker_status not in {"empty", "on the way", "assigned"}:
            worker_status = "assigned" if worker_assigned else "empty"
        wstat = f"Worker: {worker_status}"
        surface.blit(body_font.render(wstat, True, (200, 204, 214)), (layout.frame.left + _PANEL_PAD, y))
        if hasattr(building, "storage_capacity") and hasattr(building, "stored"):
            y += _ROW
            surface.blit(
                body_font.render(BuildingPanel.storage_line(building), True, (200, 204, 214)),
                (layout.frame.left + _PANEL_PAD, y),
            )

        if layout.upgrade is not None:
            u_en = layout.upgrade_enabled
            bg = (64, 110, 168) if u_en else (52, 56, 64)
            fg = (240, 242, 250) if u_en else (130, 134, 142)
            pygame.draw.rect(surface, bg, layout.upgrade, border_radius=6)
            lbl = btn_font.render(_upgrade_label(building), True, fg)
            surface.blit(
                lbl,
                (
                    layout.upgrade.centerx - lbl.get_width() // 2,
                    layout.upgrade.centery - lbl.get_height() // 2,
                ),
            )

        if layout.demolish is not None:
            pygame.draw.rect(surface, (140, 48, 52), layout.demolish, border_radius=6)
            dl = btn_font.render("Demolish", True, (255, 240, 240))
            surface.blit(
                dl,
                (
                    layout.demolish.centerx - dl.get_width() // 2,
                    layout.demolish.centery - dl.get_height() // 2,
                ),
            )

    @staticmethod
    def click_action(
        surface: pygame.Surface,
        pos: tuple[int, int],
        building: Building,
        resources: ResourceManager,
        *,
        worker_assigned: bool,
        show_upgrade: bool | None = None,
        show_demolish: bool = True,
        extra_bottom_px: int = 0,
    ) -> str | None:
        """Return ``\"close\"``, ``\"upgrade\"``, ``\"demolish\"``, or ``None``."""
        layout = BuildingPanel.layout(
            surface,
            building,
            resources,
            worker_assigned=worker_assigned,
            show_upgrade=show_upgrade,
            show_demolish=show_demolish,
            extra_bottom_px=extra_bottom_px,
        )
        x, y = pos
        if layout.close.collidepoint(x, y):
            return "close"
        if layout.upgrade is not None and layout.upgrade.collidepoint(x, y):
            return "upgrade" if layout.upgrade_enabled else None
        if layout.demolish is not None and layout.demolish.collidepoint(x, y):
            return "demolish"
        return None

    @staticmethod
    def storage_line(building: Building) -> str:
        stored = int(getattr(building, "stored"))
        capacity = int(building.storage_capacity())
        return f"Storage: {stored} / {capacity}"
