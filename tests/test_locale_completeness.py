"""Locale completeness contract: matching key sets and non-empty values (T463)."""

from __future__ import annotations

import json
from pathlib import Path


def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _locale_path(code: str) -> Path:
    return _project_root() / "src" / "game" / "settings" / "locales" / f"{code}.json"


def _load_locale(code: str) -> dict[str, str]:
    data = json.loads(_locale_path(code).read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return {str(key): str(value) for key, value in data.items()}


def test_en_and_ru_locale_files_parse() -> None:
    for code in ("en", "ru"):
        locale = _load_locale(code)
        assert locale


def test_en_and_ru_have_identical_key_sets() -> None:
    en_keys = set(_load_locale("en"))
    ru_keys = set(_load_locale("ru"))
    missing_in_ru = sorted(en_keys - ru_keys)
    missing_in_en = sorted(ru_keys - en_keys)
    assert not missing_in_ru, f"ru.json missing keys: {missing_in_ru}"
    assert not missing_in_en, f"en.json missing keys: {missing_in_en}"


def test_locale_values_are_non_empty_strings() -> None:
    for code in ("en", "ru"):
        locale = _load_locale(code)
        for key, value in locale.items():
            assert isinstance(value, str), f"{code}:{key} must be a string"
            assert value.strip(), f"{code}:{key} must not be empty or whitespace-only"
