"""Locale file schema and sample-key contract tests (T439)."""

from __future__ import annotations

import json
from pathlib import Path

SAMPLE_KEYS = (
    "ui.button.start",
    "resource.wood",
    "research.1.name",
)

COMMON_UI_KEYS = (
    "ui.button.start",
    "ui.button.upgrade",
    "ui.button.demolish",
    "ui.button.close",
    "ui.button.back",
    "ui.common.active",
    "ui.common.inactive",
    "ui.common.cost",
    "ui.common.status",
    "ui.common.storage",
    "ui.common.requirements",
    "ui.common.free",
    "ui.common.unavailable",
    "ui.window.caption",
)


def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _locale_path(code: str) -> Path:
    return _project_root() / "src" / "game" / "settings" / "locales" / f"{code}.json"


def _load_locale(code: str) -> dict[str, str]:
    data = json.loads(_locale_path(code).read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def test_en_locale_parses_and_contains_sample_keys() -> None:
    locale = _load_locale("en")
    for key in SAMPLE_KEYS:
        assert key in locale
        assert isinstance(locale[key], str)
        assert locale[key].strip()


def test_ru_locale_parses_and_contains_sample_keys() -> None:
    locale = _load_locale("ru")
    for key in SAMPLE_KEYS:
        assert key in locale
        assert isinstance(locale[key], str)
        assert locale[key].strip()


def test_both_locales_contain_common_ui_keys() -> None:
    for code in ("en", "ru"):
        locale = _load_locale(code)
        for key in COMMON_UI_KEYS:
            assert key in locale
            assert isinstance(locale[key], str)
            assert locale[key].strip()
