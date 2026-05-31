"""Laboratory panel: scientist slot grid and standard building actions."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import pygame

from game import i18n
from game.assets import worker_ui_icon
from game.buildings.laboratory import Laboratory
from game.research_state import ResearchState
from game.ui.building_panel import BuildingPanel, BuildingPanelLayout, draw_upgrade_cost_tooltip
from game.ui.panel_i18n import active_toggle_label
from game.ui.fonts import ui_font
from game.ui.laboratory_panel_research import (
    SECTION_PAD,
    draw_research_storage_section,
    research_storage_section_height,
)
from game.worker_models import Worker

_PANEL_W = 420
_PANEL_PAD = 16
_SLOT_TILE_W = 48
_SLOT_TILE_H = 42
_SLOT_GAP = 8
_SLOT_ROW_GAP = 8
_HEADER_H = 24
_TOGGLE_H = 32
_TOGGLE_GAP = 8


def scientist_slot_states(capacity: int, active_scientists: Sequence[Worker]) -> tuple[bool, ...]:
    """Per-slot fill flags: True when a Scientist occupies the slot."""
    if capacity <= 0:
        return ()
    filled = min(len(active_scientists), capacity)
    return tuple(index < filled for index in range(capacity))


def scientist_slots_summary(*, active_count: int, capacity: int) -> str:
    return i18n.t("ui.laboratory.scientists", active=int(active_count), capacity=int(capacity))


def scientist_slot_label(*, assigned: bool) -> str:
    key = "ui.laboratory.slot_sci" if assigned else "ui.laboratory.slot_empty"
    return i18n.t(key)


def _scientist_section_px(slot_capacity: int) -> int:
    if slot_capacity <= 0:
        return _HEADER_H + 16
    width = _PANEL_W - _PANEL_PAD * 2
    cols = max(1, (width + _SLOT_GAP) // (_SLOT_TILE_W + _SLOT_GAP))
    rows = (slot_capacity + cols - 1) // cols
    return _HEADER_H + rows * (_SLOT_TILE_H + _SLOT_ROW_GAP) + 16


def _extra_bottom_px(
    slot_capacity: int,
    laboratory: Laboratory,
    *,
    research_state: ResearchState | None = None,
) -> int:
    return _scientist_section_px(slot_capacity) + research_storage_section_height(
        laboratory,
        research_state=research_state,
    ) + _TOGGLE_H + _TOGGLE_GAP


@dataclass(frozen=True, slots=True)
class LaboratoryPanelLayout:
    frame: pygame.Rect
    close: pygame.Rect
    upgrade: pygame.Rect | None
    upgrade_enabled: bool
    demolish: pygame.Rect | None
    toggle: pygame.Rect
    research_section: pygame.Rect | None
    scientist_tiles: tuple[pygame.Rect, ...]
    scientist_slot_states: tuple[bool, ...]


class LaboratoryPanel:
    @staticmethod
    def supports_building(building: object) -> bool:
        return isinstance(building, Laboratory)

    @staticmethod
    def _scientist_tiles(
        base_layout: BuildingPanelLayout,
        slots: int,
        *,
        laboratory: Laboratory,
        research_state: ResearchState | None = None,
    ) -> tuple[pygame.Rect, ...]:
        if slots <= 0:
            return ()
        base_frame = base_layout.frame
        width = base_frame.width - _PANEL_PAD * 2
        cols = max(1, (width + _SLOT_GAP) // (_SLOT_TILE_W + _SLOT_GAP))
        left = base_frame.left + _PANEL_PAD
        research_h = research_storage_section_height(
            laboratory,
            research_state=research_state,
        )
        content_top = LaboratoryPanel._extra_content_top(
            base_layout,
            slots,
            laboratory=laboratory,
            research_state=research_state,
        )
        top = content_top + research_h + (SECTION_PAD if research_h > 0 else 0)
        tiles: list[pygame.Rect] = []
        for index in range(slots):
            row = index // cols
            col = index % cols
            x = left + col * (_SLOT_TILE_W + _SLOT_GAP)
            y = top + _HEADER_H + row * (_SLOT_TILE_H + _SLOT_ROW_GAP)
            tiles.append(pygame.Rect(x, y, _SLOT_TILE_W, _SLOT_TILE_H))
        return tuple(tiles)

    @staticmethod
    def _extra_content_bottom(base_layout: BuildingPanelLayout) -> int:
        action_tops = [
            rect.top
            for rect in (base_layout.upgrade, base_layout.demolish)
            if rect is not None
        ]
        if action_tops:
            return min(action_tops) - _SLOT_ROW_GAP
        return base_layout.frame.bottom - _PANEL_PAD

    @staticmethod
    def _extra_content_top(
        base_layout: BuildingPanelLayout,
        slots: int,
        *,
        laboratory: Laboratory,
        research_state: ResearchState | None = None,
    ) -> int:
        return LaboratoryPanel._extra_content_bottom(base_layout) - _extra_bottom_px(
            slots,
            laboratory,
            research_state=research_state,
        )

    @staticmethod
    def _research_section_rect(
        base_layout: BuildingPanelLayout,
        slots: int,
        *,
        laboratory: Laboratory,
        research_state: ResearchState | None = None,
    ) -> pygame.Rect | None:
        research_h = research_storage_section_height(
            laboratory,
            research_state=research_state,
        )
        if research_h <= 0:
            return None
        top = LaboratoryPanel._extra_content_top(
            base_layout,
            slots,
            laboratory=laboratory,
            research_state=research_state,
        ) + SECTION_PAD
        return pygame.Rect(
            base_layout.frame.left,
            top,
            base_layout.frame.width,
            max(0, research_h - SECTION_PAD),
        )

    @staticmethod
    def layout(
        surface: pygame.Surface,
        laboratory: Laboratory,
        *,
        worker_assigned: bool,
        production_status: str | None = None,
        worker_manager: Any | None = None,
        research_state: ResearchState | None = None,
    ) -> LaboratoryPanelLayout:
        capacity = laboratory.scientist_slot_capacity()
        base = BuildingPanel.layout(
            surface,
            laboratory,
            worker_assigned=worker_assigned,
            production_status=production_status,
            extra_bottom_px=_extra_bottom_px(
                capacity,
                laboratory,
                research_state=research_state,
            ),
        )
        active: tuple[Worker, ...] = ()
        if worker_manager is not None and not laboratory.is_under_construction:
            active = worker_manager.laboratory_research_contributing_scientists(laboratory)
        states = scientist_slot_states(capacity, active)
        upgrade_enabled = base.upgrade_enabled and not (
            research_state is not None and research_state.has_active_research()
        )
        toggle = pygame.Rect(
            base.frame.left + _PANEL_PAD,
            base.frame.bottom - _PANEL_PAD - _TOGGLE_H,
            base.frame.width - _PANEL_PAD * 2,
            _TOGGLE_H,
        )
        return LaboratoryPanelLayout(
            frame=base.frame,
            close=base.close,
            upgrade=base.upgrade,
            upgrade_enabled=upgrade_enabled,
            demolish=base.demolish,
            toggle=toggle,
            research_section=LaboratoryPanel._research_section_rect(
                base,
                capacity,
                laboratory=laboratory,
                research_state=research_state,
            ),
            scientist_tiles=LaboratoryPanel._scientist_tiles(
                base,
                capacity,
                laboratory=laboratory,
                research_state=research_state,
            ),
            scientist_slot_states=states,
        )

    @staticmethod
    def draw(
        surface: pygame.Surface,
        laboratory: Laboratory,
        *,
        worker_assigned: bool,
        worker_status: str = "empty",
        production_status: str | None = None,
        worker_manager: Any | None = None,
        research_state: ResearchState | None = None,
    ) -> LaboratoryPanelLayout:
        capacity = laboratory.scientist_slot_capacity()
        layout = LaboratoryPanel.layout(
            surface,
            laboratory,
            worker_assigned=worker_assigned,
            production_status=production_status,
            worker_manager=worker_manager,
            research_state=research_state,
        )
        BuildingPanel.draw(
            surface,
            laboratory,
            worker_assigned=worker_assigned,
            worker_status=worker_status,
            production_status=production_status,
            extra_bottom_px=_extra_bottom_px(
                capacity,
                laboratory,
                research_state=research_state,
            ),
        )
        if layout.upgrade is not None and not layout.upgrade_enabled:
            btn_font = ui_font(22)
            pygame.draw.rect(surface, (52, 56, 64), layout.upgrade, border_radius=6)
            label = btn_font.render(
                i18n.t("ui.building.upgrade_level", level=laboratory.level + 1),
                True,
                (130, 134, 142),
            )
            surface.blit(
                label,
                (
                    layout.upgrade.centerx - label.get_width() // 2,
                    layout.upgrade.centery - label.get_height() // 2,
                ),
            )
        draw_upgrade_cost_tooltip(surface, laboratory, layout.upgrade)
        if layout.research_section is not None and research_state is not None:
            draw_research_storage_section(
                surface,
                layout.frame,
                laboratory,
                research_state=research_state,
                section_top=layout.research_section.top,
            )
        body = ui_font(20)
        active: tuple[Worker, ...] = ()
        if worker_manager is not None and not laboratory.is_under_construction:
            active = worker_manager.laboratory_research_contributing_scientists(laboratory)
        summary = scientist_slots_summary(active_count=len(active), capacity=capacity)
        header_y = layout.scientist_tiles[0].top - _HEADER_H if layout.scientist_tiles else layout.frame.bottom - 40
        surface.blit(body.render(summary, True, (200, 204, 214)), (layout.frame.left + _PANEL_PAD, header_y))

        for index, tile in enumerate(layout.scientist_tiles):
            assigned = (
                index < len(layout.scientist_slot_states)
                and layout.scientist_slot_states[index]
            )
            bg = (74, 84, 96) if assigned else (52, 58, 66)
            pygame.draw.rect(surface, bg, tile, border_radius=4)
            pygame.draw.rect(surface, (116, 124, 136), tile, width=1, border_radius=4)
            label = scientist_slot_label(assigned=assigned)
            if assigned and index < len(active):
                scientist = active[index]
                icon = worker_ui_icon(scientist.type_tag, size=20)
                surface.blit(
                    icon,
                    (
                        tile.left + (tile.width - icon.get_width()) // 2,
                        tile.top + 4,
                    ),
                )
            text = ui_font(15).render(label, True, (220, 224, 232))
            surface.blit(
                text,
                (tile.centerx - text.get_width() // 2, tile.bottom - text.get_height() - 4),
            )
        active_bg = (84, 112, 84) if laboratory.active else (92, 64, 64)
        pygame.draw.rect(surface, active_bg, layout.toggle, border_radius=6)
        toggle_label = body.render(active_toggle_label(laboratory.active), True, (240, 242, 250))
        surface.blit(
            toggle_label,
            (
                layout.toggle.centerx - toggle_label.get_width() // 2,
                layout.toggle.centery - toggle_label.get_height() // 2,
            ),
        )
        return layout

    @staticmethod
    def click_action(
        surface: pygame.Surface,
        pos: tuple[int, int],
        laboratory: Laboratory,
        *,
        worker_assigned: bool,
        production_status: str | None = None,
        worker_manager: Any | None = None,
        research_state: ResearchState | None = None,
    ) -> str | None:
        layout = LaboratoryPanel.layout(
            surface,
            laboratory,
            worker_assigned=worker_assigned,
            production_status=production_status,
            worker_manager=worker_manager,
            research_state=research_state,
        )
        x, y = pos
        if layout.close.collidepoint(x, y):
            return "close"
        if layout.upgrade is not None and layout.upgrade.collidepoint(x, y):
            return "upgrade" if layout.upgrade_enabled else None
        if layout.demolish is not None and layout.demolish.collidepoint(x, y):
            return "demolish"
        if layout.toggle.collidepoint(x, y):
            return "toggle_active"
        for tile in layout.scientist_tiles:
            if tile.collidepoint(x, y):
                return None
        return None
