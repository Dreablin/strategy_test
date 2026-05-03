"""Tests for core game configuration constants."""

from game import config


def test_config_constants_match_spec() -> None:
    assert config.TICK_MS == 10_000
    assert config.TILE_W == 64
    assert config.TILE_H == 32
    assert config.GRID_SIZE == 110
    assert config.GATHER_RESOURCE_SEARCH_RADIUS == 20
    assert config.TOWN_HALL_STARTING_WAREHOUSE == {
        "wheat": 15,
        "wood": 15,
        "stone": 10,
        "iron": 5,
        "boards": 10,
        "flour": 0,
        "bread": 0,
    }
    assert config.TOWN_HALL_MIN_LEVEL_FOR_BUILDING["STONE_MINE"] == 1
    assert config.TOWN_HALL_MIN_LEVEL_FOR_BUILDING["WELL"] == 1
    assert config.TOWN_HALL_MIN_LEVEL_FOR_HIRE["MINER"] == 5
    assert config.TOWN_HALL_MIN_LEVEL_FOR_HIRE["BAKER"] == 1
    assert config.MAX_LEVEL == 10
    assert config.WINDOW_SIZE == (1280, 720)
