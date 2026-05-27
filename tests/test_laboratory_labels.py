"""Laboratory display label tests (T398)."""

from __future__ import annotations

from game.ui.building_panel import _DESCRIPTION, _DISPLAY_NAME as BUILDING_DISPLAY_NAME
from game.ui.construction_panel import _DISPLAY_NAME as CONSTRUCTION_DISPLAY_NAME
from game.ui.population_panel import _BUILDING_LABEL as POPULATION_BUILDING_LABEL
from game.ui.worker_panel import _BUILDING_LABEL as WORKER_BUILDING_LABEL


def test_laboratory_building_panel_display_name_and_description() -> None:
    assert BUILDING_DISPLAY_NAME["LABORATORY"] == "Laboratory"
    description = _DESCRIPTION["LABORATORY"]
    assert description
    assert "research" in description.lower()
    assert "scientist" in description.lower()


def test_laboratory_construction_panel_display_name() -> None:
    assert CONSTRUCTION_DISPLAY_NAME["LABORATORY"] == "Laboratory"


def test_laboratory_worker_and_population_panel_labels() -> None:
    assert WORKER_BUILDING_LABEL["LABORATORY"] == "Laboratory"
    assert POPULATION_BUILDING_LABEL["LABORATORY"] == "Laboratory"
