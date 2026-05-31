"""Tests for WINEMAKER display assets and labels (T344)."""

from __future__ import annotations

import pygame

from game import i18n
from game.assets import hire_ui_icon, worker_ui_icon
from game.ui.population_panel import _FILTER_WORKER_TYPES
from game.ui.worker_labels import worker_display_label


def test_winemaker_worker_ui_icon_returns_surface() -> None:
    icon = worker_ui_icon("WINEMAKER", size=24)
    assert isinstance(icon, pygame.Surface)
    assert icon.get_width() == 24
    assert icon.get_height() == 24


def test_winemaker_hire_ui_icon_returns_surface() -> None:
    icon = hire_ui_icon("WINEMAKER", size=20)
    assert isinstance(icon, pygame.Surface)
    assert icon.get_width() == 20
    assert icon.get_height() == 20


def test_winemaker_display_label_en() -> None:
    assert worker_display_label("WINEMAKER") == i18n.t("worker.WINEMAKER")


def test_winemaker_display_label_ru(use_locale) -> None:
    with use_locale("ru"):
        assert worker_display_label("WINEMAKER") == i18n.t("worker.WINEMAKER")


def test_winemaker_in_population_filter_worker_types() -> None:
    assert "WINEMAKER" in _FILTER_WORKER_TYPES
