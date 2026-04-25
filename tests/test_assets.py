"""Smoke tests for procedural asset surfaces."""

from game.assets import (
    building_sprite,
    grass_tile,
    resource_icon,
    tree_tile,
    worker_dot,
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


def test_tree_tile_smoke() -> None:
    _assert_nonempty_surface(tree_tile())


def test_building_sprite_smoke() -> None:
    for b_type in ("town_hall", "lumber_camp", "stone_mine", "iron_mine", "farm"):
        for level in (1, 5, 10):
            _assert_nonempty_surface(building_sprite(b_type, level))


def test_worker_dot_smoke() -> None:
    for w_type in ("LUMBERJACK", "STONECUTTER", "MINER", "FARMER"):
        _assert_nonempty_surface(worker_dot(w_type))


def test_resource_icon_smoke() -> None:
    for name in ("food", "wood", "stone", "iron"):
        _assert_nonempty_surface(resource_icon(name))
