"""Loader behavior tests for game.i18n (T440 — RED until T441)."""

from __future__ import annotations

from game import i18n


def test_default_locale_is_russian() -> None:
    assert i18n.get_locale() == "ru"


def test_set_locale_loads_explicit_russian() -> None:
    i18n.set_locale("ru")
    try:
        assert i18n.get_locale() == "ru"
        assert i18n.t("ui.button.start") == "Начать"
    finally:
        i18n.set_locale("en")


def test_t_returns_russian_string_in_default_locale() -> None:
    assert i18n.get_locale() == "ru"
    assert i18n.t("ui.button.start") == "Начать"


def test_t_falls_back_to_english_from_ru_for_en_only_key() -> None:
    i18n.set_locale("ru")
    try:
        ru_catalog = i18n._loaded["ru"]
        saved = ru_catalog.pop("ui.test.en_only_fallback")
        try:
            assert i18n.t("ui.test.en_only_fallback") == "English only"
        finally:
            ru_catalog["ui.test.en_only_fallback"] = saved
    finally:
        i18n.set_locale("en")


def test_t_returns_key_id_when_missing() -> None:
    missing = "ui.missing.key.xyz"
    assert i18n.t(missing) == missing


def test_t_substitutes_params() -> None:
    assert i18n.t("ui.test.labeled_count", name="Дерево", count=34) == "Дерево: 34"


def test_t_returns_unformatted_template_on_missing_param() -> None:
    assert i18n.t("ui.test.labeled_count", name="Дерево") == "{name}: {count}"
