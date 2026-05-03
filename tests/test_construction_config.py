"""Construction requirements config contract tests (T185)."""

from game import config


def test_construction_requirements_cover_all_building_types() -> None:
    expected = {
        "LUMBER_CAMP",
        "STONE_MINE",
        "IRON_MINE",
        "FARM",
        "FORESTER_HUT",
        "SCHOOL",
        "HOUSE",
        "SAWMILL",
        "MILL",
        "BAKERY",
        "WELL",
    }
    assert set(config.CONSTRUCTION_REQUIREMENTS) == expected


def test_construction_requirements_have_levels_1_to_10() -> None:
    for b_type, levels in config.CONSTRUCTION_REQUIREMENTS.items():
        expected = {1} if b_type == "WELL" else set(range(1, 11))
        assert set(levels) == expected, b_type


def test_construction_spec_values_are_non_negative_and_have_build_time() -> None:
    for levels in config.CONSTRUCTION_REQUIREMENTS.values():
        for spec in levels.values():
            assert spec.build_time_ms > 0
            for amount in spec.cost.values():
                assert amount >= 0
