"""Tests for shared building panel i18n helpers."""

from __future__ import annotations

from game import i18n
from game.ui.panel_i18n import (
    active_toggle_label,
    blocked_line,
    flow_line,
    production_line,
    resource_amount_line,
)
from game.ui.winery_panel import WineryPanel
from game.buildings.winery import Winery


def test_resource_amount_line_uses_locale_labels() -> None:
    line = resource_amount_line("grapes", 2, 5)
    assert line == i18n.t(
        "ui.panel.amount_line",
        label=i18n.t("resource.grapes"),
        amount=2,
        capacity=5,
    )


def test_flow_line_input_output_roles() -> None:
    wheat = flow_line(role_key="ui.panel.input", resource_key="wheat", amount=1, capacity=3)
    assert i18n.t("ui.panel.input") in wheat
    assert i18n.t("resource.wheat") in wheat


def test_blocked_and_production_lines() -> None:
    assert i18n.t("status.no_worker") in blocked_line("no worker")
    assert i18n.t("status.processing") in production_line("processing")


def test_winery_storage_lines_localized() -> None:
    winery = Winery(level=1, grid_pos=(4, 4))
    grapes_line, wine_line = WineryPanel.storage_lines(winery)
    assert i18n.t("resource.grapes") in grapes_line
    assert i18n.t("resource.wine") in wine_line


def test_active_toggle_label_ru(use_locale) -> None:
    with use_locale("ru"):
        assert active_toggle_label(True) == "Активно"
        assert active_toggle_label(False) == "Неактивно"
