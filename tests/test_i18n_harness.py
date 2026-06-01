"""Locale-switch test harness (T442)."""

from __future__ import annotations

from game import i18n


def test_use_locale_returns_english_then_russian_for_same_key(use_locale) -> None:
    key = "ui.button.start"
    with use_locale("en"):
        assert i18n.get_locale() == "en"
        assert i18n.t(key) == "Start"
    with use_locale("ru"):
        assert i18n.get_locale() == "ru"
        assert i18n.t(key) == "Начать"
    assert i18n.get_locale() == "ru"


def test_use_locale_restores_after_nested_switch(use_locale) -> None:
    key = "resource.wood"
    with use_locale("ru"):
        assert i18n.t(key) == "Дерево"
    assert i18n.get_locale() == "ru"
