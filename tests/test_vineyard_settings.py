"""Vineyard plot building JSON is loaded into config (T319)."""

from __future__ import annotations

import json
from pathlib import Path

from game import config
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.buildings.vineyard import Vineyard
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.world import World


def _vineyard_json() -> dict:
    root = Path(__file__).resolve().parents[1]
    path = root / "src" / "game" / "settings" / "buildings" / "vineyard.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_vineyard_settings_registered_under_upper_type_tag() -> None:
    assert "VINEYARD" in config.BUILDING_SETTINGS
    assert config.building_setting("VINEYARD", "building_type") == "VINEYARD"


def test_vineyard_footprint_is_one_by_one() -> None:
    fp = config.building_setting("VINEYARD", "footprint")
    assert fp["tiles_w"] == 1
    assert fp["tiles_h"] == 1


def test_vineyard_plot_does_not_block_its_tile() -> None:
    world = World(world_seed=0)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    world._iron.clear()  # noqa: SLF001
    world.refresh_passability_tile_caches()
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    tile = near_town_hall_tile(12, 8)
    plot = registry.place(Vineyard, tile)

    assert plot.grid_pos == tile
    assert not world.is_occupied(*tile)
    assert tile not in world.blocked_tiles()


def test_vineyard_growth_stages_and_duration_from_json() -> None:
    assert config.building_int_setting("VINEYARD", "growth", "stage_count") == 4
    assert config.building_int_setting("VINEYARD", "growth", "stage_duration_ms") == 45_000


def test_vineyard_asset_defaults_match_disk_meta_shape() -> None:
    raw = _vineyard_json()["asset_defaults"]
    loaded = config.building_setting("VINEYARD", "asset_defaults")
    assert loaded == raw
    assert float(loaded["scale"]) == 1.0
    assert loaded["anchor_norm"] == [0.5, 1.0]
    assert loaded["offset_px"] == [0, 0]


def test_vineyard_level_one_construction_is_one_board() -> None:
    spec = config.CONSTRUCTION_REQUIREMENTS["VINEYARD"][1]
    assert spec.cost == {"boards": 1}
    assert spec.build_time_ms == 12_000


def test_vineyard_construction_levels_match_json() -> None:
    configured = _vineyard_json()["levels"]
    loaded = config.CONSTRUCTION_REQUIREMENTS["VINEYARD"]
    assert set(loaded) == set(range(1, 11))
    for level_key, payload in configured.items():
        spec = loaded[int(level_key)]
        assert spec.cost == payload["cost"]
        assert spec.build_time_ms == payload["build_time_ms"]
