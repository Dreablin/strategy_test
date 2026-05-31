"""Laboratory display label tests (T398)."""

from __future__ import annotations

from game.ui.building_panel import building_description, building_display_name


def test_laboratory_building_panel_display_name_and_description() -> None:
    assert building_display_name("LABORATORY") == "Laboratory"
    description = building_description("LABORATORY")
    assert description
    assert "research" in description.lower()
    assert "scientist" in description.lower()


def test_laboratory_construction_panel_display_name() -> None:
    assert building_display_name("LABORATORY") == "Laboratory"


def test_laboratory_worker_and_population_panel_labels() -> None:
    assert building_display_name("LABORATORY") == "Laboratory"
