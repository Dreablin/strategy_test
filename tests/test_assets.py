"""Smoke tests and loader behavior checks for asset surfaces."""

from pathlib import Path
import os
import time

import pygame

import game.assets as assets_mod
from game.assets import (
    building_sprite_construction,
    building_sprite,
    building_sprite_anchor,
    clear_asset_caches,
    grass_tile,
    hire_ui_icon,
    population_icon,
    resource_icon,
    tree_sprite,
    tree_sprite_anchor,
    tree_sprite_offset,
    worker_dot,
    worker_ui_icon,
)


def _assert_nonempty_surface(surf) -> None:
    assert surf.get_width() > 0
    assert surf.get_height() > 0
    found = False
    for x in range(0, surf.get_width(), max(1, surf.get_width() // 8)):
        for y in range(0, surf.get_height(), max(1, surf.get_height() // 8)):
            c = surf.get_at((x, y))
            a = c.a if hasattr(c, "a") else c[3]
            if a > 0 and sum(c[:3]) > 0:
                found = True
                break
        if found:
            break
    assert found


def test_grass_tile_smoke() -> None:
    _assert_nonempty_surface(grass_tile())
    assert grass_tile() is grass_tile()


def test_building_sprite_smoke() -> None:
    for b_type in (
        "town_hall",
        "lumber_camp",
        "stone_mine",
        "iron_mine",
        "farm",
        "mill",
        "school",
        "bakery",
        "well",
        "chicken_farm",
        "cow_farm",
        "canteen",
    ):
        for level in (1, 5, 10):
            spr = building_sprite(b_type, level)
            _assert_nonempty_surface(spr)
            ax, ay = building_sprite_anchor(b_type, level)
            assert 0 <= ax <= spr.get_width()
            assert 0 <= ay <= spr.get_height()


def test_cow_farm_disk_meta_and_sprite_smoke() -> None:
    """T297: meta on disk; ready + construction sprites resolve (procedural fallback)."""
    root = Path(__file__).resolve().parents[1] / "assets" / "buildings" / "cow_farm"
    assert (root / "asset_meta.json").is_file()

    for b_tag in ("cow_farm", "COW_FARM"):
        for level in (1, 5, 10):
            spr = building_sprite(b_tag, level)
            _assert_nonempty_surface(spr)
            ax, ay = building_sprite_anchor(b_tag, level)
            assert 0 <= ax <= spr.get_width()
            assert 0 <= ay <= spr.get_height()
        for target_level in (1, 10):
            cspr = building_sprite_construction(b_tag, target_level)
            _assert_nonempty_surface(cspr)
            cax, cay = assets_mod.building_sprite_construction_anchor(b_tag, target_level)
            assert 0 <= cax <= cspr.get_width()
            assert 0 <= cay <= cspr.get_height()


def test_canteen_disk_placeholders_and_sprite_smoke() -> None:
    """T250/T251: disk placeholders; built/construction sprites and anchors (CANTEEN type_tag)."""
    root = Path(__file__).resolve().parents[1] / "assets" / "buildings" / "canteen"
    assert (root / "asset_meta.json").is_file()
    assert (root / "default.png").is_file()
    assert (root / "construction.png").is_file()

    for b_tag in ("canteen", "CANTEEN"):
        for level in (1, 5, 10):
            spr = building_sprite(b_tag, level)
            _assert_nonempty_surface(spr)
            ax, ay = building_sprite_anchor(b_tag, level)
            assert 0 <= ax <= spr.get_width()
            assert 0 <= ay <= spr.get_height()
        for target_level in (1, 10):
            cspr = building_sprite_construction(b_tag, target_level)
            _assert_nonempty_surface(cspr)
            cax, cay = assets_mod.building_sprite_construction_anchor(b_tag, target_level)
            assert 0 <= cax <= cspr.get_width()
            assert 0 <= cay <= cspr.get_height()


def test_worker_dot_smoke() -> None:
    for w_type in (
        "LUMBERJACK",
        "STONECUTTER",
        "MINER",
        "FARMER",
        "ANIMAL_HERDER",
        "MILLER",
        "BAKER",
        "WATERMAN",
    ):
        _assert_nonempty_surface(worker_dot(w_type))


def test_lumberjack_worker_dot_supports_carrying_variant() -> None:
    empty = worker_dot("LUMBERJACK", carrying=False)
    carrying = worker_dot("LUMBERJACK", carrying=True)
    _assert_nonempty_surface(empty)
    _assert_nonempty_surface(carrying)
    assert empty is not carrying


def test_lumberjack_worker_dot_fallback_exists_for_empty_and_carrying(tmp_path, monkeypatch) -> None:
    root = tmp_path / "npc"
    monkeypatch.setattr(assets_mod, "_NPC_ROOT", root)
    clear_asset_caches()
    empty = worker_dot("LUMBERJACK", carrying=False)
    carrying = worker_dot("LUMBERJACK", carrying=True)
    _assert_nonempty_surface(empty)
    _assert_nonempty_surface(carrying)
    clear_asset_caches()


def test_stonecutter_worker_dot_supports_carrying_variant() -> None:
    empty = worker_dot("STONECUTTER", carrying=False)
    carrying = worker_dot("STONECUTTER", carrying=True)
    _assert_nonempty_surface(empty)
    _assert_nonempty_surface(carrying)
    assert empty is not carrying


def test_stonecutter_worker_dot_fallback_has_dedicated_stone_carry_helper(tmp_path, monkeypatch) -> None:
    root = tmp_path / "npc"
    monkeypatch.setattr(assets_mod, "_NPC_ROOT", root)
    clear_asset_caches()

    # Phase-12 contract: stonecutter carry fallback is a dedicated stone payload
    # variant, not the generic carry box used by other workers.
    assert hasattr(assets_mod, "_procedural_worker_carry_stone_dot")

    empty = worker_dot("STONECUTTER", carrying=False)
    carrying = worker_dot("STONECUTTER", carrying=True)
    _assert_nonempty_surface(empty)
    _assert_nonempty_surface(carrying)
    clear_asset_caches()


def test_stonecutter_worker_dot_prefers_stonecutter_folder_layout(tmp_path, monkeypatch) -> None:
    root = tmp_path / "npc"
    folder = root / "stonecutter"
    _write_png(folder / "default.png", (11, 11), (20, 120, 160))
    _write_png(folder / "carrying.png", (13, 13), (140, 140, 150))
    monkeypatch.setattr(assets_mod, "_NPC_ROOT", root)
    clear_asset_caches()
    empty = worker_dot("STONECUTTER", carrying=False)
    carrying = worker_dot("STONECUTTER", carrying=True)
    assert empty.get_size() == (11, 11)
    assert carrying.get_size() == (13, 13)
    clear_asset_caches()


def test_lumberjack_worker_dot_cache_invalidation_by_mtime(tmp_path, monkeypatch) -> None:
    root = tmp_path / "npc"
    folder = root / "lumberjack"
    _write_png(folder / "default.png", (10, 10), (10, 120, 10))
    _write_png(folder / "carrying.png", (12, 12), (120, 10, 10))
    monkeypatch.setattr(assets_mod, "_NPC_ROOT", root)
    clear_asset_caches()
    first = worker_dot("LUMBERJACK", carrying=True)
    assert first.get_size() == (12, 12)

    updated = folder / "carrying.png"
    _write_png(updated, (18, 18), (120, 10, 10))
    # Ensure mtime changes on fast filesystems.
    now = time.time() + 1.0
    os.utime(updated, (now, now))
    second = worker_dot("LUMBERJACK", carrying=True)
    assert second.get_size() == (18, 18)
    clear_asset_caches()


def test_resource_icon_smoke() -> None:
    for name in ("wheat", "wood", "stone", "iron", "flour", "bread", "water"):
        _assert_nonempty_surface(resource_icon(name))


def test_population_icon_smoke() -> None:
    _assert_nonempty_surface(population_icon(24))


def test_population_icon_falls_back_procedural_when_disk_asset_missing(tmp_path, monkeypatch) -> None:
    root = tmp_path / "ui"
    monkeypatch.setattr(assets_mod, "_UI_ROOT", root)
    clear_asset_caches()
    _assert_nonempty_surface(population_icon(24))
    clear_asset_caches()


def test_worker_and_hire_ui_icon_smoke() -> None:
    for w_type in (
        "LUMBERJACK",
        "STONECUTTER",
        "MINER",
        "FARMER",
        "ANIMAL_HERDER",
        "MILLER",
        "BAKER",
        "WATERMAN",
    ):
        _assert_nonempty_surface(worker_ui_icon(w_type, 24))
        _assert_nonempty_surface(hire_ui_icon(w_type, 20))


def _write_png(path: Path, size: tuple[int, int], color: tuple[int, int, int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    surf = pygame.Surface(size, pygame.SRCALPHA)
    surf.fill((*color, 255))
    pygame.image.save(surf, str(path))


def test_building_sprite_prefers_level_file_over_default(tmp_path, monkeypatch) -> None:
    root = tmp_path / "buildings"
    farm_dir = root / "farm"
    _write_png(farm_dir / "default.png", (20, 20), (200, 10, 10))
    _write_png(farm_dir / "level_01.png", (30, 30), (10, 200, 10))
    (farm_dir / "asset_meta.json").write_text("{}", encoding="utf-8")

    monkeypatch.setattr(assets_mod, "_BUILDINGS_ROOT", root)
    clear_asset_caches()
    spr = building_sprite("FARM", 1)
    assert spr.get_size() == (30, 30)
    clear_asset_caches()


def test_field_empty_sprite_can_use_level_zero_file(tmp_path, monkeypatch) -> None:
    root = tmp_path / "buildings"
    field_dir = root / "field"
    _write_png(field_dir / "default.png", (20, 20), (200, 10, 10))
    _write_png(field_dir / "level_00.png", (31, 29), (10, 200, 10))
    monkeypatch.setattr(assets_mod, "_BUILDINGS_ROOT", root)
    clear_asset_caches()
    spr = building_sprite("FIELD", 0)
    assert spr.get_size() == (31, 29)
    clear_asset_caches()


def test_building_sprite_applies_scale_and_anchor_norm(tmp_path, monkeypatch) -> None:
    root = tmp_path / "buildings"
    farm_dir = root / "farm"
    _write_png(farm_dir / "default.png", (100, 80), (120, 90, 60))
    (farm_dir / "asset_meta.json").write_text(
        '{"default":{"scale":0.5,"anchor_norm":[0.25,0.75]},"levels":{}}',
        encoding="utf-8",
    )

    monkeypatch.setattr(assets_mod, "_BUILDINGS_ROOT", root)
    clear_asset_caches()
    spr = building_sprite("FARM", 1)
    ax, ay = building_sprite_anchor("FARM", 1)
    assert spr.get_size() == (50, 40)
    assert (ax, ay) == (12, 30)
    clear_asset_caches()


def test_building_sprite_construction_prefers_level_file_then_generic(tmp_path, monkeypatch) -> None:
    root = tmp_path / "buildings"
    farm_dir = root / "farm"
    _write_png(farm_dir / "construction.png", (20, 20), (200, 10, 10))
    _write_png(farm_dir / "construction_2.png", (34, 26), (10, 200, 10))
    monkeypatch.setattr(assets_mod, "_BUILDINGS_ROOT", root)
    clear_asset_caches()
    spr = building_sprite_construction("FARM", 2)
    assert spr.get_size() == (34, 26)
    clear_asset_caches()


def test_building_sprite_construction_falls_back_to_procedural_overlay(tmp_path, monkeypatch) -> None:
    root = tmp_path / "buildings"
    monkeypatch.setattr(assets_mod, "_BUILDINGS_ROOT", root)
    clear_asset_caches()
    spr = building_sprite_construction("FORESTER_HUT", 3)
    _assert_nonempty_surface(spr)
    # Fallback should still be visibly non-opaque after alpha blend.
    sample = spr.get_at((spr.get_width() // 2, spr.get_height() // 2))
    assert sample.a < 255
    clear_asset_caches()


def test_building_meta_bom_is_accepted(tmp_path, monkeypatch) -> None:
    root = tmp_path / "buildings"
    farm_dir = root / "farm"
    _write_png(farm_dir / "default.png", (64, 64), (100, 100, 100))
    # Write with BOM (utf-8-sig) to mirror typical Windows editor behavior.
    (farm_dir / "asset_meta.json").write_text(
        '{"default":{"scale":0.25,"anchor_norm":[0.5,1.0]},"levels":{}}',
        encoding="utf-8-sig",
    )

    monkeypatch.setattr(assets_mod, "_BUILDINGS_ROOT", root)
    clear_asset_caches()
    spr = building_sprite("FARM", 1)
    assert spr.get_size() == (16, 16)
    clear_asset_caches()


def test_tree_sprite_loads_stage_file_when_present() -> None:
    clear_asset_caches()
    spr = tree_sprite("sapling")
    _assert_nonempty_surface(spr)


def test_tree_sprite_falls_back_procedural_when_stage_missing(tmp_path, monkeypatch) -> None:
    root = tmp_path / "trees"
    monkeypatch.setattr(assets_mod, "_TREES_ROOT", root)
    clear_asset_caches()
    spr = tree_sprite("adult")
    _assert_nonempty_surface(spr)
    clear_asset_caches()


def test_tree_sprite_applies_species_stage_meta_scale_and_anchor(tmp_path, monkeypatch) -> None:
    root = tmp_path / "trees"
    _write_png(root / "species_2" / "sapling" / "default.png", (100, 80), (70, 140, 90))
    (root / "asset_meta.json").write_text(
        (
            "{"
            "\"default\":{\"scale\":1.0,\"anchor_norm\":[0.5,1.0]},"
            "\"stages\":{},"
            "\"species\":{"
            "\"2\":{\"default\":{\"scale\":1.0,\"anchor_norm\":[0.5,1.0]},"
            "\"stages\":{\"sapling\":{\"scale\":0.5,\"anchor_norm\":[0.25,0.75],\"offset_px\":[3,-2]}}}"
            "}"
            "}"
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(assets_mod, "_TREES_ROOT", root)
    clear_asset_caches()
    spr = tree_sprite("sapling", species=2)
    ax, ay = tree_sprite_anchor("sapling", species=2)
    ox, oy = tree_sprite_offset("sapling", species=2)
    assert spr.get_size() == (50, 40)
    assert (ax, ay) == (12, 30)
    assert (ox, oy) == (3, -2)
    clear_asset_caches()
