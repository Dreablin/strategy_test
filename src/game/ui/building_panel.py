"""Centered modal panel: building info, upgrade/demolish actions, close control."""

from __future__ import annotations

from dataclasses import dataclass

import pygame

from game import i18n
from game.buildings.base import Building
from game.config import CONSTRUCTION_REQUIREMENTS
from game.research_config import RESEARCH_BY_ID
from game.resource_catalog import resource_display_label
from game.statue_research import statue_stage_research_id
from game.worker_status import localized_status
from game.ui.worker_labels import building_worker_status_line
from game.ui.fonts import ui_font
_PANEL_W = 420
_PANEL_PAD = 16
_ROW = 26
_BTN_H = 36
_CLOSE = 28
_TOOLTIP_PAD = 8
_TOOLTIP_GAP = 4
_TOOLTIP_BG = (22, 26, 34)
_TOOLTIP_BORDER = (72, 78, 92)
_TOOLTIP_TEXT = (220, 224, 232)


def building_display_name(type_tag: str) -> str:
    tag = str(type_tag).upper()
    locale_key = f"building.{tag}.name"
    label = i18n.t(locale_key)
    if label != locale_key:
        return label
    return tag.replace("_", " ").title()


def building_description(type_tag: str) -> str:
    tag = str(type_tag).upper()
    locale_key = f"building.{tag}.desc"
    label = i18n.t(locale_key)
    if label != locale_key:
        return label
    return ""


def _upgrade_label(building: Building) -> str:
    next_stage_name = getattr(building, "next_stage_name", None)
    if callable(next_stage_name):
        stage = next_stage_name()
        if stage:
            return i18n.t("ui.statue.start_stage", stage=stage)
    nxt = building.level + 1
    return i18n.t("ui.building.upgrade_level", level=nxt)


def _upgrade_cost_lines(building: Building) -> tuple[str, ...]:
    upgrade_cost = i18n.t("ui.building.upgrade_cost")
    nxt = int(building.level) + 1
    spec = CONSTRUCTION_REQUIREMENTS.get(building.type_tag, {}).get(nxt)
    if spec is None:
        lines = [f"{upgrade_cost}: {i18n.t('ui.common.unavailable')}"]
    else:
        items = [(resource, amount) for resource, amount in sorted(spec.cost.items()) if int(amount) > 0]
        if not items:
            lines = [f"{upgrade_cost}: {i18n.t('ui.common.free')}"]
        else:
            lines = [f"{upgrade_cost}:"]
            for resource, amount in items:
                lines.append(f"{resource_display_label(resource)}: {int(amount)}")
    if building.type_tag == "STATUE":
        research_id = statue_stage_research_id(nxt)
        if research_id is not None:
            research = RESEARCH_BY_ID.get(research_id)
            name = research.name if research is not None else research_id
            lines.append(i18n.t("ui.common.requires_research", name=name))
    return tuple(lines)


def draw_upgrade_cost_tooltip(
    surface: pygame.Surface,
    building: Building,
    upgrade_rect: pygame.Rect | None,
    *,
    hover_pos: tuple[int, int] | None = None,
) -> pygame.Rect | None:
    if upgrade_rect is None:
        return None
    if hover_pos is None:
        hover_pos = pygame.mouse.get_pos()
    if not upgrade_rect.collidepoint(hover_pos):
        return None
    font = ui_font(18)
    line_surfaces = [font.render(line, True, _TOOLTIP_TEXT) for line in _upgrade_cost_lines(building)]
    max_w = max(surf.get_width() for surf in line_surfaces)
    total_h = sum(surf.get_height() for surf in line_surfaces) + _TOOLTIP_GAP * (len(line_surfaces) - 1)
    box_w = max_w + _TOOLTIP_PAD * 2
    box_h = total_h + _TOOLTIP_PAD * 2
    x = upgrade_rect.right + 8
    if x + box_w > surface.get_width() - 4:
        x = max(4, upgrade_rect.left - box_w - 8)
    y = upgrade_rect.top
    if y + box_h > surface.get_height() - 4:
        y = max(4, surface.get_height() - box_h - 4)
    box = pygame.Rect(x, y, box_w, box_h)
    pygame.draw.rect(surface, _TOOLTIP_BG, box, border_radius=4)
    pygame.draw.rect(surface, _TOOLTIP_BORDER, box, width=1, border_radius=4)
    line_y = box.top + _TOOLTIP_PAD
    for surf in line_surfaces:
        surface.blit(surf, (box.left + _TOOLTIP_PAD, line_y))
        line_y += surf.get_height() + _TOOLTIP_GAP
    return box


def worker_status_line(building: Building, worker_status: str) -> str:
    return building_worker_status_line(building.type_tag, worker_status)


@dataclass(frozen=True, slots=True)
class BuildingPanelLayout:
    """Hit targets and outer frame for the modal (shared by draw and click handling)."""

    frame: pygame.Rect
    close: pygame.Rect
    upgrade: pygame.Rect | None
    upgrade_enabled: bool
    demolish: pygame.Rect | None


class BuildingPanel:
    """PRD §3 F-UI-PANEL-02: name, level, description, worker row, actions, ×."""

    @staticmethod
    def layout(
        surface: pygame.Surface,
        building: Building,
        *,
        worker_assigned: bool,
        production_status: str | None = None,
        show_upgrade: bool | None = None,
        show_demolish: bool = True,
        extra_bottom_px: int = 0,
        upgrade_enabled_override: bool | None = None,
    ) -> BuildingPanelLayout:
        sw, sh = surface.get_size()
        cls = type(building)
        max_lv = cls.max_level()
        if show_upgrade is None:
            show_upgrade = building.level < max_lv
        can_upgrade = bool(show_upgrade and building.level < max_lv)
        upgrade_enabled = can_upgrade
        if upgrade_enabled_override is not None:
            upgrade_enabled = bool(can_upgrade and upgrade_enabled_override)

        has_storage_row = hasattr(building, "storage_capacity") and hasattr(building, "stored")
        has_status_row = production_status is not None
        text_rows = 4 + int(has_storage_row) + int(has_status_row)
        btn_count = int(can_upgrade) + int(show_demolish)
        positioned_btn_count = btn_count
        if (
            extra_bottom_px > 0
            and show_demolish
            and not can_upgrade
            and building.level >= max_lv
            and max_lv > 1
        ):
            positioned_btn_count += 1
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

        y = frame.bottom - _PANEL_PAD - (positioned_btn_count * (_BTN_H + 8) if positioned_btn_count else 0)
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
        *,
        worker_assigned: bool,
        worker_status: str = "empty",
        production_status: str | None = None,
        worker_working: bool = False,
        show_upgrade: bool | None = None,
        show_demolish: bool = True,
        extra_bottom_px: int = 0,
        upgrade_enabled_override: bool | None = None,
    ) -> None:
        layout = BuildingPanel.layout(
            surface,
            building,
            worker_assigned=worker_assigned,
            production_status=production_status,
            show_upgrade=show_upgrade,
            show_demolish=show_demolish,
            extra_bottom_px=extra_bottom_px,
            upgrade_enabled_override=upgrade_enabled_override,
        )
        dim = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        dim.fill((10, 12, 16, 170))
        surface.blit(dim, (0, 0))

        pygame.draw.rect(surface, (36, 40, 52), layout.frame, border_radius=10)
        pygame.draw.rect(surface, (72, 78, 92), layout.frame, width=2, border_radius=10)

        title_font = ui_font(28)
        body_font = ui_font(22)
        btn_font = ui_font(22)

        name = building_display_name(building.type_tag)
        stage_name = getattr(building, "stage_name", None)
        if callable(stage_name):
            title_text = i18n.t("ui.building.panel_title_stage", name=name, stage=stage_name())
        else:
            title_text = i18n.t("ui.building.panel_title", name=name, level=building.level)
        title = title_font.render(title_text, True, (238, 240, 248))
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
        desc = building_description(building.type_tag)
        surface.blit(body_font.render(desc, True, (200, 204, 214)), (layout.frame.left + _PANEL_PAD, y))
        y += _ROW
        allowed_worker_status = {"empty", "on_the_way", "assigned"}
        if building.type_tag in {"FARM", "VINEYARD_FARM"}:
            allowed_worker_status = allowed_worker_status | {
                "moving",
                "resting",
                "sowing",
                "harvesting",
            }
        if worker_status not in allowed_worker_status:
            worker_status = "assigned" if worker_assigned else "empty"
        wstat = worker_status_line(building, worker_status)
        surface.blit(body_font.render(wstat, True, (200, 204, 214)), (layout.frame.left + _PANEL_PAD, y))
        if hasattr(building, "storage_capacity") and hasattr(building, "stored"):
            y += _ROW
            surface.blit(
                body_font.render(BuildingPanel.storage_line(building), True, (200, 204, 214)),
                (layout.frame.left + _PANEL_PAD, y),
            )
        if production_status is not None:
            y += _ROW
            surface.blit(
                body_font.render(
                    i18n.t("ui.common.status_line", status=localized_status(production_status)),
                    True,
                    (200, 204, 214),
                ),
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
            dl = btn_font.render(i18n.t("ui.button.demolish"), True, (255, 240, 240))
            surface.blit(
                dl,
                (
                    layout.demolish.centerx - dl.get_width() // 2,
                    layout.demolish.centery - dl.get_height() // 2,
                ),
            )
        draw_upgrade_cost_tooltip(surface, building, layout.upgrade)

    @staticmethod
    def click_action(
        surface: pygame.Surface,
        pos: tuple[int, int],
        building: Building,
        *,
        worker_assigned: bool,
        production_status: str | None = None,
        show_upgrade: bool | None = None,
        show_demolish: bool = True,
        extra_bottom_px: int = 0,
        upgrade_enabled_override: bool | None = None,
    ) -> str | None:
        """Return ``\"close\"``, ``\"upgrade\"``, ``\"demolish\"``, or ``None``."""
        layout = BuildingPanel.layout(
            surface,
            building,
            worker_assigned=worker_assigned,
            production_status=production_status,
            show_upgrade=show_upgrade,
            show_demolish=show_demolish,
            extra_bottom_px=extra_bottom_px,
            upgrade_enabled_override=upgrade_enabled_override,
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
        return i18n.t("ui.common.storage_line", stored=stored, capacity=capacity)
