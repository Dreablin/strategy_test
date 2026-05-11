"""Vineyard plot disk assets and growth-stage sprites (T322)."""

from __future__ import annotations

from pathlib import Path

import game.assets as assets_mod
from game.assets import building_sprite, building_sprite_anchor, building_sprite_construction


def _assert_nonempty_surface(surf) -> None:
    assert surf.get_width() > 0 and surf.get_height() > 0
    found = False
    for x in range(0, surf.get_width(), max(1, surf.get_width() // 6)):
        for y in range(0, surf.get_height(), max(1, surf.get_height() // 6)):
            c = surf.get_at((x, y))
            a = c.a if hasattr(c, "a") else c[3]
            if a > 0 and sum(c[:3]) > 0:
                found = True
                break
        if found:
            break
    assert found


def test_vineyard_disk_meta_exists() -> None:
    root = Path(__file__).resolve().parents[1] / "assets" / "buildings" / "vineyard"
    assert (root / "asset_meta.json").is_file()


def test_vineyard_growth_stage_sprites_and_anchors() -> None:
    for b_tag in ("vineyard", "VINEYARD"):
        for stage in (1, 2, 3, 4):
            spr = building_sprite(b_tag, stage)
            _assert_nonempty_surface(spr)
            ax, ay = building_sprite_anchor(b_tag, stage)
            assert 0 <= ax <= spr.get_width()
            assert 0 <= ay <= spr.get_height()


def test_vineyard_high_level_clamps_to_final_growth_sprite() -> None:
    """Levels above 4 map to the ripe stage for a single asset path."""
    a = building_sprite("VINEYARD", 10)
    b = building_sprite("VINEYARD", 4)
    assert a.get_size() == b.get_size()


def test_vineyard_construction_sprite_smoke() -> None:
    for b_tag in ("vineyard", "VINEYARD"):
        for target in (1, 4):
            cspr = building_sprite_construction(b_tag, target)
            _assert_nonempty_surface(cspr)
            cax, cay = assets_mod.building_sprite_construction_anchor(b_tag, target)
            assert 0 <= cax <= cspr.get_width()
            assert 0 <= cay <= cspr.get_height()
