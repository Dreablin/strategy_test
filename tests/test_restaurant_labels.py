"""Tests for Restaurant display labels/descriptions (T370)."""

from __future__ import annotations


def test_restaurant_building_panel_display_name() -> None:
    from game.ui.building_panel import _DISPLAY_NAME
    assert _DISPLAY_NAME.get("RESTAURANT") == "Restaurant"


def test_restaurant_building_panel_description() -> None:
    from game.ui.building_panel import _DESCRIPTION
    assert "RESTAURANT" in _DESCRIPTION
    assert "elite" in _DESCRIPTION["RESTAURANT"].lower()


def test_restaurant_population_panel_label() -> None:
    from game.ui.population_panel import _BUILDING_LABEL
    assert _BUILDING_LABEL.get("RESTAURANT") == "Restaurant"


def test_restaurant_worker_panel_label() -> None:
    from game.ui.worker_panel import _BUILDING_LABEL
    assert _BUILDING_LABEL.get("RESTAURANT") == "Restaurant"
