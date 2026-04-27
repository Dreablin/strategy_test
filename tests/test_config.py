"""Tests for core game configuration constants."""

from game import config


def test_config_constants_match_spec() -> None:
    assert config.TICK_MS == 10_000
    assert config.TILE_W == 64
    assert config.TILE_H == 32
    assert config.GRID_SIZE == 32
    assert config.INITIAL_RESOURCES == {
        "food": 200,
        "wood": 200,
        "stone": 0,
        "iron": 0,
    }
    assert config.WORKER_HIRE_COST == {"food": 5}
    assert config.BUILD_COST_WOOD == 5
    assert config.BUILD_COSTS["STONE_MINE"] == {"wood": 5}
    assert config.WORKER_HIRE_COSTS["MINER"] == {"food": 5}
    assert config.TOWN_HALL_MIN_LEVEL_FOR_BUILDING["STONE_MINE"] == 3
    assert config.TOWN_HALL_MIN_LEVEL_FOR_HIRE["MINER"] == 5
    assert config.MAX_LEVEL == 10
    assert config.WINDOW_SIZE == (1280, 720)
