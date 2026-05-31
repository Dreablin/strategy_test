"""Laboratory display label tests (T398)."""

from __future__ import annotations

from game import i18n
from game.ui.building_panel import building_description, building_display_name
from game.ui.laboratory_panel import scientist_slots_summary


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


def test_laboratory_scientists_summary_ru(use_locale) -> None:
    with use_locale("ru"):
        assert scientist_slots_summary(active_count=2, capacity=5) == "Учёные: 2 / 5"
        assert i18n.t("ui.laboratory.active_research") == "Активное исследование"
