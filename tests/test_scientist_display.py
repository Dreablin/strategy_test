"""Tests for SCIENTIST display assets and labels (T400)."""

from __future__ import annotations

import pygame

from game.assets import hire_ui_icon, worker_ui_icon
from game.ui.population_panel import _FILTER_WORKER_TYPES
from game.ui.population_panel import _WORKER_LABEL as POP_WORKER_LABEL  # noqa: N811
from game.ui.worker_panel import _WORKER_LABEL as WP_WORKER_LABEL  # noqa: N811


def test_scientist_worker_ui_icon_returns_surface() -> None:
    icon = worker_ui_icon("SCIENTIST", size=24)
    assert isinstance(icon, pygame.Surface)
    assert icon.get_width() == 24
    assert icon.get_height() == 24


def test_scientist_hire_ui_icon_returns_surface() -> None:
    icon = hire_ui_icon("SCIENTIST", size=20)
    assert isinstance(icon, pygame.Surface)
    assert icon.get_width() == 20
    assert icon.get_height() == 20


def test_scientist_in_population_panel_labels() -> None:
    assert "SCIENTIST" in POP_WORKER_LABEL
    assert POP_WORKER_LABEL["SCIENTIST"] == "Scientist"


def test_scientist_in_worker_panel_labels() -> None:
    assert "SCIENTIST" in WP_WORKER_LABEL
    assert WP_WORKER_LABEL["SCIENTIST"] == "Scientist"


def test_scientist_in_population_filter_worker_types() -> None:
    assert "SCIENTIST" in _FILTER_WORKER_TYPES
