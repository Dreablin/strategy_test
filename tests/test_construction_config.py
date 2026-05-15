"""Construction requirements config contract tests (T185)."""

from game import config


def test_construction_requirements_cover_all_building_types() -> None:
    expected = {
        b_type
        for b_type, payload in config.BUILDING_SETTINGS.items()
        if isinstance(payload, dict) and "levels" in payload
    }
    assert set(config.CONSTRUCTION_REQUIREMENTS) == expected


def test_construction_requirements_have_contiguous_levels_from_one() -> None:
    for b_type, levels in config.CONSTRUCTION_REQUIREMENTS.items():
        top_level = max(levels)
        assert set(levels) == set(range(1, top_level + 1)), b_type


def test_construction_spec_values_are_non_negative_and_have_build_time() -> None:
    for levels in config.CONSTRUCTION_REQUIREMENTS.values():
        for spec in levels.values():
            assert spec.build_time_ms > 0
            for amount in spec.cost.values():
                assert amount >= 0
