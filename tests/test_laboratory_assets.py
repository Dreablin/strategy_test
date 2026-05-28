"""Tests for Laboratory asset loading/fallback (T396)."""

from __future__ import annotations

from pathlib import Path

import pygame

import game.assets as assets_mod
from game.assets import building_sprite, building_sprite_anchor, building_sprite_construction


def _assert_nonempty_surface(surface: pygame.Surface) -> None:
    assert surface.get_width() > 0
    assert surface.get_height() > 0


def test_laboratory_asset_meta_exists() -> None:
    root = Path(__file__).resolve().parents[1] / "assets" / "buildings" / "laboratory"
    assert (root / "asset_meta.json").is_file()


def test_laboratory_completed_sprite_resolves() -> None:
    for level in (1, 5, 10):
        sprite = building_sprite("LABORATORY", level)
        _assert_nonempty_surface(sprite)
        anchor_x, anchor_y = building_sprite_anchor("LABORATORY", level)
        assert 0 <= anchor_x <= sprite.get_width()
        assert 0 <= anchor_y <= sprite.get_height()


def test_laboratory_construction_sprite_resolves() -> None:
    for target_level in (1, 10):
        sprite = building_sprite_construction("LABORATORY", target_level)
        _assert_nonempty_surface(sprite)
        anchor_x, anchor_y = assets_mod.building_sprite_construction_anchor(
            "LABORATORY", target_level
        )
        assert 0 <= anchor_x <= sprite.get_width()
        assert 0 <= anchor_y <= sprite.get_height()


def test_laboratory_building_folder_mapped() -> None:
    from game.assets import _BUILDING_FOLDER

    assert _BUILDING_FOLDER.get("LABORATORY") == "laboratory"
