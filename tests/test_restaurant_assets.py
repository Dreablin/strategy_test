"""Tests for Restaurant asset loading/fallback (T368)."""

from __future__ import annotations

from pathlib import Path

import pygame

import game.assets as assets_mod
from game.assets import building_sprite, building_sprite_anchor, building_sprite_construction


def _assert_nonempty_surface(s: pygame.Surface) -> None:
    assert s.get_width() > 0
    assert s.get_height() > 0


def test_restaurant_asset_meta_exists() -> None:
    root = Path(__file__).resolve().parents[1] / "assets" / "buildings" / "restaurant"
    assert (root / "asset_meta.json").is_file()


def test_restaurant_completed_sprite_resolves() -> None:
    for level in (1, 5, 10):
        spr = building_sprite("RESTAURANT", level)
        _assert_nonempty_surface(spr)
        ax, ay = building_sprite_anchor("RESTAURANT", level)
        assert 0 <= ax <= spr.get_width()
        assert 0 <= ay <= spr.get_height()


def test_restaurant_construction_sprite_resolves() -> None:
    for target_level in (1, 10):
        cspr = building_sprite_construction("RESTAURANT", target_level)
        _assert_nonempty_surface(cspr)
        cax, cay = assets_mod.building_sprite_construction_anchor("RESTAURANT", target_level)
        assert 0 <= cax <= cspr.get_width()
        assert 0 <= cay <= cspr.get_height()


def test_restaurant_building_folder_mapped() -> None:
    from game.assets import _BUILDING_FOLDER

    assert _BUILDING_FOLDER.get("RESTAURANT") == "restaurant"
