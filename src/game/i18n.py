"""Internationalization: locale file loader and ``t()`` lookup."""

from __future__ import annotations

import json
from pathlib import Path

from game.config import SETTINGS

_LOCALES_DIR = Path(__file__).resolve().parent / "settings" / "locales"
_current_locale: str = str(SETTINGS.get("locale", "en"))
_loaded: dict[str, dict[str, str]] = {}


def _load_locale_file(code: str) -> dict[str, str]:
    if code in _loaded:
        return _loaded[code]
    path = _LOCALES_DIR / f"{code}.json"
    if not path.exists():
        _loaded[code] = {}
        return _loaded[code]
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Locale file must be a JSON object: {path}")
    strings = {str(key): str(value) for key, value in data.items()}
    _loaded[code] = strings
    return strings


def get_locale() -> str:
    return _current_locale


def set_locale(code: str) -> None:
    global _current_locale
    _current_locale = code
    _load_locale_file(code)


def _lookup(key: str, locale: str) -> str | None:
    value = _load_locale_file(locale).get(key)
    if value is None or not value.strip():
        return None
    return value


def t(key: str, **params: object) -> str:
    template = _lookup(key, _current_locale)
    if template is None and _current_locale != "en":
        template = _lookup(key, "en")
    if template is None:
        return key
    if not params:
        return template
    try:
        return template.format(**params)
    except KeyError:
        return template


_load_locale_file(_current_locale)
_load_locale_file("en")
