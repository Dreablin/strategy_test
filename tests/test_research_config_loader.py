"""Research config loader and validation tests (T388)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from game import i18n
from game.research_config import (
    RESEARCH_BY_ID,
    RESEARCH_DEFINITIONS,
    ResearchDefinition,
    load_research_definitions,
)


def test_load_default_research_definitions() -> None:
    definitions = load_research_definitions()
    assert len(definitions) >= 4
    assert all(isinstance(entry, ResearchDefinition) for entry in definitions)


def test_module_level_research_catalog_matches_loader() -> None:
    assert RESEARCH_DEFINITIONS == load_research_definitions()
    assert set(RESEARCH_BY_ID) == {entry.id for entry in RESEARCH_DEFINITIONS}
    for entry in RESEARCH_DEFINITIONS:
        assert RESEARCH_BY_ID[entry.id] is entry


def test_technology_entries_are_accessible_by_id() -> None:
    for tech_id in ("1", "2", "3", "4"):
        entry = RESEARCH_BY_ID[tech_id]
        assert entry.tier == int(tech_id)
        assert entry.column == 0
        assert entry.resource_cost
        assert entry.required_points > 0
        assert entry.image_key
        assert entry.name == i18n.t(f"research.{tech_id}.name")
        assert entry.effect_text == i18n.t(f"research.{tech_id}.effect")


def test_all_research_definitions_resolve_locale_copy() -> None:
    for entry in RESEARCH_DEFINITIONS:
        assert entry.name == i18n.t(f"research.{entry.id}.name")
        assert entry.description == i18n.t(f"research.{entry.id}.desc")
        assert entry.effect_text == i18n.t(f"research.{entry.id}.effect")
        assert entry.name.strip()
        assert entry.description.strip()
        assert entry.effect_text.strip()


def test_research_copy_ru_locale(use_locale) -> None:
    with use_locale("ru"):
        entry = next(e for e in load_research_definitions() if e.id == "1")
        assert entry.name == "Технология I"
        assert "1-го уровня" in entry.effect_text


def _write_config(tmp_path: Path, researches: list[dict]) -> Path:
    path = tmp_path / "research.json"
    path.write_text(json.dumps({"researches": researches}), encoding="utf-8")
    return path


def test_load_rejects_duplicate_ids(tmp_path: Path) -> None:
    path = _write_config(
        tmp_path,
        [
            {
                "id": "a",
                "name": "A",
                "description": "A",
                "effect_text": "A effect",
                "tier": 1,
                "column": 0,
                "dependencies": [],
                "resource_cost": {"wood": 1},
                "required_points": 10,
                "image_key": "a",
            },
            {
                "id": "a",
                "name": "B",
                "description": "B",
                "effect_text": "B effect",
                "tier": 2,
                "column": 1,
                "dependencies": [],
                "resource_cost": {"wood": 1},
                "required_points": 10,
                "image_key": "b",
            },
        ],
    )
    with pytest.raises(ValueError, match="duplicate research id"):
        load_research_definitions(path)


def test_load_rejects_tier_out_of_range(tmp_path: Path) -> None:
    path = _write_config(
        tmp_path,
        [
            {
                "id": "x",
                "name": "X",
                "description": "X",
                "effect_text": "X effect",
                "tier": 5,
                "column": 0,
                "dependencies": [],
                "resource_cost": {"wood": 1},
                "required_points": 10,
                "image_key": "x",
            },
        ],
    )
    with pytest.raises(ValueError, match="tier must be in"):
        load_research_definitions(path)


def test_load_rejects_missing_column(tmp_path: Path) -> None:
    path = _write_config(
        tmp_path,
        [
            {
                "id": "x",
                "name": "X",
                "description": "X",
                "effect_text": "X effect",
                "tier": 1,
                "dependencies": [],
                "resource_cost": {"wood": 1},
                "required_points": 10,
                "image_key": "x",
            },
        ],
    )
    with pytest.raises(ValueError, match="column must be an integer"):
        load_research_definitions(path)


def test_load_rejects_empty_resource_cost(tmp_path: Path) -> None:
    path = _write_config(
        tmp_path,
        [
            {
                "id": "x",
                "name": "X",
                "description": "X",
                "effect_text": "X effect",
                "tier": 1,
                "column": 0,
                "dependencies": [],
                "resource_cost": {},
                "required_points": 10,
                "image_key": "x",
            },
        ],
    )
    with pytest.raises(ValueError, match="resource_cost must be a non-empty object"):
        load_research_definitions(path)


def test_load_rejects_non_positive_required_points(tmp_path: Path) -> None:
    path = _write_config(
        tmp_path,
        [
            {
                "id": "x",
                "name": "X",
                "description": "X",
                "effect_text": "X effect",
                "tier": 1,
                "column": 0,
                "dependencies": [],
                "resource_cost": {"wood": 1},
                "required_points": 0,
                "image_key": "x",
            },
        ],
    )
    with pytest.raises(ValueError, match="required_points must be a positive integer"):
        load_research_definitions(path)


def test_load_rejects_empty_image_key(tmp_path: Path) -> None:
    path = _write_config(
        tmp_path,
        [
            {
                "id": "x",
                "name": "X",
                "description": "X",
                "effect_text": "X effect",
                "tier": 1,
                "column": 0,
                "dependencies": [],
                "resource_cost": {"wood": 1},
                "required_points": 10,
                "image_key": "",
            },
        ],
    )
    with pytest.raises(ValueError, match="image_key must be a non-empty string"):
        load_research_definitions(path)


def test_load_rejects_missing_locale_copy_without_json_fallback(tmp_path: Path) -> None:
    path = _write_config(
        tmp_path,
        [
            {
                "id": "x",
                "tier": 1,
                "column": 0,
                "dependencies": [],
                "resource_cost": {"wood": 1},
                "required_points": 10,
                "image_key": "x",
            },
        ],
    )
    with pytest.raises(ValueError, match="missing locale key"):
        load_research_definitions(path)


def test_load_rejects_unknown_dependency_reference(tmp_path: Path) -> None:
    path = _write_config(
        tmp_path,
        [
            {
                "id": "x",
                "name": "X",
                "description": "X",
                "effect_text": "X effect",
                "tier": 1,
                "column": 0,
                "dependencies": ["missing"],
                "resource_cost": {"wood": 1},
                "required_points": 10,
                "image_key": "x",
            },
        ],
    )
    with pytest.raises(ValueError, match="unknown dependency"):
        load_research_definitions(path)


def test_load_rejects_self_dependency(tmp_path: Path) -> None:
    path = _write_config(
        tmp_path,
        [
            {
                "id": "x",
                "name": "X",
                "description": "X",
                "effect_text": "X effect",
                "tier": 1,
                "column": 0,
                "dependencies": ["x"],
                "resource_cost": {"wood": 1},
                "required_points": 10,
                "image_key": "x",
            },
        ],
    )
    with pytest.raises(ValueError, match="cannot depend on itself"):
        load_research_definitions(path)


def test_load_rejects_unknown_worker_effect_stat(tmp_path: Path) -> None:
    path = _write_config(
        tmp_path,
        [
            {
                "id": "x",
                "name": "X",
                "description": "X",
                "effect_text": "X effect",
                "tier": 1,
                "column": 0,
                "dependencies": [],
                "resource_cost": {"wood": 1},
                "required_points": 10,
                "image_key": "x",
                "worker_effects": {
                    "by_type": {"CARRIER": {"not_a_stat": 0.1}},
                },
            },
        ],
    )
    with pytest.raises(ValueError, match="unknown worker effect stat"):
        load_research_definitions(path)
