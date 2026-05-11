"""Tests for Winery display labels and descriptions (T350)."""

from __future__ import annotations

from game.ui.building_panel import _DISPLAY_NAME, _DESCRIPTION  # noqa: N811
from game.ui.worker_panel import _BUILDING_LABEL as WP_BUILDING_LABEL  # noqa: N811
from game.ui.population_panel import _BUILDING_LABEL as POP_BUILDING_LABEL  # noqa: N811


def test_winery_display_name() -> None:
    assert "WINERY" in _DISPLAY_NAME
    assert _DISPLAY_NAME["WINERY"] == "Winery"


def test_winery_description() -> None:
    assert "WINERY" in _DESCRIPTION
    assert "wine" in _DESCRIPTION["WINERY"].lower()


def test_winery_in_worker_panel_building_labels() -> None:
    assert "WINERY" in WP_BUILDING_LABEL
    assert WP_BUILDING_LABEL["WINERY"] == "Winery"


def test_winery_in_population_panel_building_labels() -> None:
    assert "WINERY" in POP_BUILDING_LABEL
    assert POP_BUILDING_LABEL["WINERY"] == "Winery"
