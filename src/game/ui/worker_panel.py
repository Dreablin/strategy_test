"""Centered modal panel: worker state and current transport task."""

from __future__ import annotations

from dataclasses import dataclass

import pygame

from game import i18n
from game.resource_catalog import resource_display_label
from game.ui.building_panel import building_display_name
from game.ui.worker_labels import worker_display_label
from game.worker_models import Worker
from game.worker_satiety import MAX_WORKER_SATIETY, clamp_worker_satiety
from game.ui.fonts import ui_font

_PANEL_W = 420
_PANEL_PAD = 16
_ROW = 26
_CLOSE = 28


def _localized_state(state: str) -> str:
    key = f"status.worker.{state}"
    label = i18n.t(key)
    if label != key:
        return label
    return state


def _localized_purpose(purpose: str) -> str:
    key = f"status.worker.purpose.{purpose}"
    label = i18n.t(key)
    if label != key:
        return label
    return purpose


def _none_label() -> str:
    return i18n.t("ui.common.none")


def _building_name(building) -> str:
    if building is None:
        return _none_label()
    tag = str(getattr(building, "type_tag", ""))
    if not tag:
        return _none_label()
    return building_display_name(tag)


def _resource_name(value: str | None) -> str:
    if value is None:
        return _none_label()
    return resource_display_label(value)


def _move_speed_line(worker: Worker) -> str:
    speed = worker.effective_move_speed_mult()
    return i18n.t(
        "ui.worker.move_speed",
        mult=f"{speed:.2f}",
        travel_ms=worker.effective_travel_ms(),
    )


def _worker_lines(worker: Worker) -> list[str]:
    sat = clamp_worker_satiety(int(getattr(worker, "satiety", 0)))
    state = _localized_state(str(worker.state))
    lines = [
        i18n.t("ui.worker.state", state=state),
        i18n.t("ui.worker.satiety", current=sat, max=MAX_WORKER_SATIETY),
        _move_speed_line(worker),
        i18n.t(
            "ui.worker.assigned",
            building=_building_name(worker.assigned_building),
        ),
        i18n.t("ui.worker.carrying", resource=_resource_name(worker.carrying)),
    ]
    task = worker.transport_task
    if task is None:
        lines.append(i18n.t("ui.worker.task", task=_none_label()))
        return lines

    lines.extend(
        [
            i18n.t("ui.worker.task", task=_localized_purpose(task.purpose)),
            i18n.t("ui.worker.resource", resource=_resource_name(task.resource)),
            i18n.t("ui.worker.from", building=_building_name(task.source)),
            i18n.t("ui.worker.to", building=_building_name(task.target)),
        ]
    )
    if task.returning_to_town_hall:
        lines.append(i18n.t("ui.worker.returning_yes"))
    return lines


@dataclass(frozen=True, slots=True)
class WorkerPanelLayout:
    frame: pygame.Rect
    close: pygame.Rect


class WorkerPanel:
    """Small read-only worker panel, mirroring building modal behavior."""

    @staticmethod
    def body_lines(worker: Worker) -> list[str]:
        """Body text lines under the title (includes satiety and task summary)."""
        return _worker_lines(worker)

    @staticmethod
    def layout(surface: pygame.Surface, worker: Worker) -> WorkerPanelLayout:
        sw, sh = surface.get_size()
        row_count = len(WorkerPanel.body_lines(worker))
        h = _PANEL_PAD * 2 + _ROW + 8 + row_count * _ROW + 8
        frame = pygame.Rect(sw // 2 - _PANEL_W // 2, sh // 2 - h // 2, _PANEL_W, h)
        close = pygame.Rect(
            frame.right - _PANEL_PAD - _CLOSE,
            frame.top + _PANEL_PAD,
            _CLOSE,
            _CLOSE,
        )
        return WorkerPanelLayout(frame=frame, close=close)

    @staticmethod
    def draw(surface: pygame.Surface, worker: Worker) -> None:
        layout = WorkerPanel.layout(surface, worker)
        dim = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        dim.fill((10, 12, 16, 170))
        surface.blit(dim, (0, 0))

        pygame.draw.rect(surface, (36, 40, 52), layout.frame, border_radius=10)
        pygame.draw.rect(surface, (72, 78, 92), layout.frame, width=2, border_radius=10)

        title_font = ui_font(28)
        body_font = ui_font(22)
        title = title_font.render(worker_display_label(worker.type_tag), True, (238, 240, 248))
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

        y = layout.frame.top + _PANEL_PAD + _ROW + 8
        for line in WorkerPanel.body_lines(worker):
            surface.blit(body_font.render(line, True, (200, 204, 214)), (layout.frame.left + _PANEL_PAD, y))
            y += _ROW

    @staticmethod
    def click_action(surface: pygame.Surface, pos: tuple[int, int], worker: Worker) -> str | None:
        layout = WorkerPanel.layout(surface, worker)
        if layout.close.collidepoint(pos):
            return "close"
        return None
