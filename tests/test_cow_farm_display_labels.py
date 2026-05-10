"""Cow Farm player-facing labels (T299)."""

from __future__ import annotations

from game.ui import building_panel
from game.ui import population_panel
from game.ui import worker_panel


def test_cow_farm_building_panel_name_and_description() -> None:
    assert building_panel._DISPLAY_NAME["COW_FARM"] == "Cow Farm"  # noqa: SLF001
    desc = building_panel._DESCRIPTION["COW_FARM"]  # noqa: SLF001
    assert "beef" in desc.lower()
    assert "hide" in desc.lower()


def test_cow_farm_worker_and_population_building_labels() -> None:
    assert worker_panel._BUILDING_LABEL["COW_FARM"] == "Cow Farm"  # noqa: SLF001
    assert population_panel._BUILDING_LABEL["COW_FARM"] == "Cow Farm"  # noqa: SLF001
