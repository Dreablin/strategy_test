"""Laboratory building class shell tests (T393)."""

from __future__ import annotations

import pytest

from game.buildings.laboratory import Laboratory
from game.config import building_int_setting, building_level_int_setting


def test_laboratory_type_tag_and_footprint() -> None:
    lab = Laboratory(level=1, grid_pos=(4, 4))
    assert lab.type_tag == "LABORATORY"
    assert Laboratory.footprint == (2, 2)
    assert lab.grid_pos == (4, 4)


def test_laboratory_max_level() -> None:
    assert Laboratory.max_level() == 10
    Laboratory(level=10)
    with pytest.raises(ValueError):
        Laboratory(level=11)


def test_laboratory_scientist_slot_capacity_uses_settings() -> None:
    lab = Laboratory(level=3)
    expected = building_level_int_setting("LABORATORY", "scientist_slots", 3)
    assert lab.scientist_slot_capacity() == expected
    assert lab.scientist_slot_capacity() == 2


def test_laboratory_research_point_rate_uses_settings() -> None:
    lab = Laboratory(level=1)
    expected = building_int_setting("LABORATORY", "research", "points_per_scientist_per_second")
    assert lab.research_points_per_scientist_per_second() == expected
    assert lab.research_points_per_scientist_per_second() > 0


def test_laboratory_technology_tier_unlock_levels() -> None:
    lab = Laboratory(level=1)
    assert lab.technology_tier_unlock_level(1) == 1
    assert lab.technology_tier_unlock_level(2) == 3
    assert lab.technology_tier_unlock_level(3) == 6
    assert lab.technology_tier_unlock_level(4) == 9


def test_laboratory_unlocks_technology_tier_by_level() -> None:
    lab = Laboratory(level=1)
    assert lab.unlocks_technology_tier(1)
    assert not lab.unlocks_technology_tier(2)
    lab.level = 3
    assert lab.unlocks_technology_tier(2)
    assert not lab.unlocks_technology_tier(3)


def test_laboratory_rejects_invalid_technology_tier() -> None:
    lab = Laboratory(level=5)
    with pytest.raises(ValueError, match="technology tier must be"):
        lab.technology_tier_unlock_level(0)


def test_laboratory_research_input_storage_starts_empty() -> None:
    lab = Laboratory(level=1)
    assert not lab.has_research_input_storage()
    assert lab.research_input_resources() == ()
    assert lab.research_input_amounts() == {}


def test_laboratory_initialize_and_clear_research_input_storage() -> None:
    lab = Laboratory(level=1)
    lab.initialize_research_input_storage({"wood": 5, "boards": 3})
    assert lab.has_research_input_storage()
    assert lab.research_input_resources() == ("wood", "boards")
    assert lab.research_input_capacity("wood") == 5
    assert lab.research_input_amount("wood") == 0
    assert lab.research_input_amounts() == {"wood": 0, "boards": 0}
    lab.clear_research_input_storage()
    assert not lab.has_research_input_storage()
