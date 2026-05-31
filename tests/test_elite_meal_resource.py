"""Tests for elite_meal local-only resource label (T361)."""

from __future__ import annotations

from game import i18n
from game.resource_catalog import (
    ELITE_MEAL_KEY,
    LOCAL_ONLY_MEAL_KEYS,
    TOWN_HALL_WAREHOUSE_KEYS,
    is_local_only_meal,
    is_town_hall_warehouse_resource,
    resource_display_label,
)


def test_elite_meal_key_value() -> None:
    assert ELITE_MEAL_KEY == "elite_meal"


def test_elite_meal_has_display_label() -> None:
    label = resource_display_label("elite_meal")
    assert label == i18n.t("resource.elite_meal")


def test_wood_display_label_en() -> None:
    assert resource_display_label("wood") == i18n.t("resource.wood")


def test_simple_meal_display_label_en() -> None:
    assert resource_display_label("simple_meal") == i18n.t("resource.simple_meal")


def test_unknown_resource_falls_back_to_title_case() -> None:
    assert resource_display_label("mystery_ore") == "Mystery Ore"


def test_wood_display_label_ru(use_locale) -> None:
    with use_locale("ru"):
        assert resource_display_label("wood") == i18n.t("resource.wood")


def test_elite_meal_display_label_ru(use_locale) -> None:
    with use_locale("ru"):
        assert resource_display_label("elite_meal") == i18n.t("resource.elite_meal")


def test_elite_meal_not_in_warehouse_keys() -> None:
    assert "elite_meal" not in TOWN_HALL_WAREHOUSE_KEYS


def test_elite_meal_not_warehouse_resource() -> None:
    assert is_town_hall_warehouse_resource("elite_meal") is False


def test_elite_meal_is_local_only_meal() -> None:
    assert is_local_only_meal("elite_meal") is True


def test_simple_meal_is_local_only_meal() -> None:
    assert is_local_only_meal("simple_meal") is True


def test_bread_is_not_local_only_meal() -> None:
    assert is_local_only_meal("bread") is False


def test_local_only_meal_keys_contains_both() -> None:
    assert "simple_meal" in LOCAL_ONLY_MEAL_KEYS
    assert "elite_meal" in LOCAL_ONLY_MEAL_KEYS


def test_elite_meal_icon_color_exists() -> None:
    from game.assets import _resource_colors
    color = _resource_colors("elite_meal")
    assert isinstance(color, tuple)
    assert len(color) == 3
