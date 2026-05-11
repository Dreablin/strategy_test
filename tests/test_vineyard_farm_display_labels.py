"""Vineyard Farm player-facing labels (T318)."""

from __future__ import annotations

from game.ui import building_panel
from game.ui import population_panel
from game.ui import worker_panel


def test_vineyard_farm_building_panel_name_and_description() -> None:
    assert building_panel._DISPLAY_NAME["VINEYARD_FARM"] == "Vineyard Farm"  # noqa: SLF001
    desc = building_panel._DESCRIPTION["VINEYARD_FARM"]  # noqa: SLF001
    assert "grape" in desc.lower()
    assert "town hall" in desc.lower()


def test_vineyard_farm_worker_and_population_building_labels() -> None:
    assert worker_panel._BUILDING_LABEL["VINEYARD_FARM"] == "Vineyard Farm"  # noqa: SLF001
    assert population_panel._BUILDING_LABEL["VINEYARD_FARM"] == "Vineyard Farm"  # noqa: SLF001
