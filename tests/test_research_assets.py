"""Research asset placeholder and resolver tests (T390/T391)."""

from __future__ import annotations

from pathlib import Path

import pytest

from game.research_assets import clear_research_asset_caches, research_image, research_image_for_id
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


def _assert_nonempty_surface(surf) -> None:
    assert surf.get_width() > 0
    assert surf.get_height() > 0
    found = False
    for x in range(0, surf.get_width(), max(1, surf.get_width() // 8)):
        for y in range(0, surf.get_height(), max(1, surf.get_height() // 8)):
            color = surf.get_at((x, y))
            alpha = color.a if hasattr(color, "a") else color[3]
            if alpha > 0 and sum(color[:3]) > 0:
                found = True
                break
        if found:
            break
    assert found


@pytest.mark.parametrize("image_key", ["technology_1", "technology_2", "technology_3", "technology_4"])
def test_research_image_resolves_for_configured_keys(image_key: str) -> None:
    clear_research_asset_caches()
    surf = research_image(image_key)
    _assert_nonempty_surface(surf)
    assert surf.get_width() == 64
    assert surf.get_height() == 64


def test_research_image_for_id_resolves_all_configured_researches() -> None:
    clear_research_asset_caches()
    for entry in RESEARCH_DEFINITIONS:
        surf = research_image_for_id(entry.id, size=48)
        _assert_nonempty_surface(surf)
        assert surf.get_size() == (48, 48)


def test_research_image_procedural_fallback_when_disk_file_missing() -> None:
    clear_research_asset_caches()
    surf = research_image("missing_research_placeholder_key", size=32)
    _assert_nonempty_surface(surf)
    assert surf.get_size() == (32, 32)


def test_research_image_rejects_empty_key() -> None:
    with pytest.raises(ValueError, match="image_key must be non-empty"):
        research_image("")
