"""Vineyard plot player-facing labels (T324)."""

from __future__ import annotations

from game.ui import building_panel
from game.ui import construction_panel
from game.ui import population_panel
from game.ui import worker_panel


def test_vineyard_building_panel_name_and_description() -> None:
    assert building_panel._DISPLAY_NAME["VINEYARD"] == "Vineyard"  # noqa: SLF001
    desc = building_panel._DESCRIPTION["VINEYARD"]  # noqa: SLF001
    assert "grape" in desc.lower()
    assert "vineyard farm" in desc.lower()


def test_vineyard_worker_and_population_building_labels() -> None:
    assert worker_panel._BUILDING_LABEL["VINEYARD"] == "Vineyard"  # noqa: SLF001
    assert population_panel._BUILDING_LABEL["VINEYARD"] == "Vineyard"  # noqa: SLF001


def test_vineyard_construction_panel_display_name() -> None:
    assert construction_panel._DISPLAY_NAME["VINEYARD"] == "Vineyard"  # noqa: SLF001
