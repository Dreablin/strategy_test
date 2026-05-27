"""Compact hover tooltip for research tiles (cost, points, dependencies, lock reason)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

import pygame

from game.research_config import RESEARCH_BY_ID, ResearchDefinition
from game.resource_catalog import resource_display_label
from game.ui.research_tile_layout import ResearchTileLayout

_PAD = 8
_LINE_GAP = 2
_FONT_SIZE = 18
_BG = (22, 26, 34)
_BORDER = (72, 78, 92)
_TEXT = (220, 224, 232)
_LOCK = (220, 140, 120)


@dataclass(frozen=True, slots=True)
class ResearchTileTooltipInfo:
    resource_cost: dict[str, int]
    required_points: int
    dependency_labels: tuple[str, ...]
    lock_reason: str | None = None


def research_tooltip_info_from_entry(
    entry: ResearchDefinition,
    *,
    lock_reason: str | None = None,
) -> ResearchTileTooltipInfo:
    deps = tuple(RESEARCH_BY_ID[dep_id].name for dep_id in entry.dependencies if dep_id in RESEARCH_BY_ID)
    return ResearchTileTooltipInfo(
        resource_cost=dict(entry.resource_cost),
        required_points=entry.required_points,
        dependency_labels=deps,
        lock_reason=lock_reason,
    )


def research_tooltip_info_for_id(
    research_id: str,
    *,
    lock_reason: str | None = None,
) -> ResearchTileTooltipInfo:
    return research_tooltip_info_from_entry(RESEARCH_BY_ID[research_id], lock_reason=lock_reason)


def format_research_tooltip_lines(info: ResearchTileTooltipInfo) -> tuple[str, ...]:
    cost_parts = [
        f"{resource_display_label(res)} {amount}"
        for res, amount in sorted(info.resource_cost.items())
    ]
    cost_line = "Cost: " + (", ".join(cost_parts) if cost_parts else "none")
    points_line = f"Points: {info.required_points}"
    if info.dependency_labels:
        deps_line = "Requires: " + ", ".join(info.dependency_labels)
    else:
        deps_line = "Requires: none"
    lines: list[str] = [cost_line, points_line, deps_line]
    if info.lock_reason:
        lines.append(f"Locked: {info.lock_reason}")
    return tuple(lines)


def hovered_research_tile(
    tiles: tuple[ResearchTileLayout, ...],
    pos: tuple[int, int],
) -> ResearchTileLayout | None:
    x, y = pos
    for tile in tiles:
        if tile.tile_rect.collidepoint(x, y):
            return tile
    return None


def _tooltip_rect_for_lines(
    surface: pygame.Surface,
    anchor: pygame.Rect,
    line_surfaces: list[pygame.Surface],
) -> pygame.Rect:
    max_w = max(surf.get_width() for surf in line_surfaces)
    total_h = sum(surf.get_height() for surf in line_surfaces) + _LINE_GAP * (len(line_surfaces) - 1)
    box_w = max_w + _PAD * 2
    box_h = total_h + _PAD * 2
    x = anchor.right + 6
    y = anchor.top
    if x + box_w > surface.get_width():
        x = max(0, anchor.left - box_w - 6)
    if y + box_h > surface.get_height():
        y = max(0, surface.get_height() - box_h - 4)
    return pygame.Rect(x, y, box_w, box_h)


def draw_research_tile_tooltip(
    surface: pygame.Surface,
    anchor: pygame.Rect,
    info: ResearchTileTooltipInfo,
) -> pygame.Rect:
    """Draw tooltip near ``anchor``; return the tooltip background rect."""
    font = pygame.font.Font(None, _FONT_SIZE)
    lines = format_research_tooltip_lines(info)
    line_surfaces = [font.render(line, True, _LOCK if line.startswith("Locked:") else _TEXT) for line in lines]
    box = _tooltip_rect_for_lines(surface, anchor, line_surfaces)
    pygame.draw.rect(surface, _BG, box, border_radius=4)
    pygame.draw.rect(surface, _BORDER, box, width=1, border_radius=4)
    y = box.top + _PAD
    for surf in line_surfaces:
        surface.blit(surf, (box.left + _PAD, y))
        y += surf.get_height() + _LINE_GAP
    return box


def draw_research_tooltip_at_hover(
    surface: pygame.Surface,
    tiles: tuple[ResearchTileLayout, ...],
    hover_pos: tuple[int, int] | None,
    *,
    lock_reasons: Mapping[str, str] | None = None,
) -> pygame.Rect | None:
    """Show tooltip when ``hover_pos`` is over a tile; return tooltip rect or ``None``."""
    if hover_pos is None:
        return None
    tile = hovered_research_tile(tiles, hover_pos)
    if tile is None:
        return None
    reasons = lock_reasons if lock_reasons is not None else {}
    lock = reasons.get(tile.research_id)
    info = research_tooltip_info_for_id(tile.research_id, lock_reason=lock)
    return draw_research_tile_tooltip(surface, tile.tile_rect, info)
