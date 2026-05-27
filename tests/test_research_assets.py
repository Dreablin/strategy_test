"""Research asset placeholder filesystem tests (T390)."""

from __future__ import annotations

from pathlib import Path

from game.research_config import RESEARCH_DEFINITIONS

_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def research_asset_path(image_key: str) -> Path:
    return _project_root() / "assets" / "research" / f"{image_key}.png"


def test_research_assets_directory_exists() -> None:
    research_dir = _project_root() / "assets" / "research"
    assert research_dir.is_dir()


def test_configured_research_image_keys_have_placeholder_files() -> None:
    keys = {entry.image_key for entry in RESEARCH_DEFINITIONS}
    assert keys == {"technology_1", "technology_2", "technology_3", "technology_4"}
    for image_key in sorted(keys):
        path = research_asset_path(image_key)
        assert path.is_file(), f"missing placeholder file: {path}"
        payload = path.read_bytes()
        assert payload.startswith(_PNG_MAGIC)
        assert len(payload) > 0
