"""Research settings JSON schema tests (T387)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

_REQUIRED_ENTRY_KEYS = frozenset(
    {
        "id",
        "name",
        "description",
        "tier",
        "column",
        "dependencies",
        "resource_cost",
        "required_points",
        "image_key",
    }
)


def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _research_settings() -> dict:
    path = _project_root() / "src" / "game" / "settings" / "research.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _technology_entries() -> list[dict]:
    settings = _research_settings()
    researches = settings.get("researches")
    assert isinstance(researches, list)
    by_id = {entry["id"]: entry for entry in researches}
    return [by_id[str(i)] for i in range(1, 5)]


def test_research_settings_file_exists_and_parses() -> None:
    settings = _research_settings()
    assert "researches" in settings
    assert len(settings["researches"]) >= 4


@pytest.mark.parametrize("tech_id", ["1", "2", "3", "4"])
def test_technology_entry_has_required_fields(tech_id: str) -> None:
    settings = _research_settings()
    entry = next(r for r in settings["researches"] if r["id"] == tech_id)
    missing = _REQUIRED_ENTRY_KEYS - entry.keys()
    assert not missing, f"Technology {tech_id} missing keys: {sorted(missing)}"
    assert isinstance(entry["name"], str) and entry["name"]
    assert isinstance(entry["description"], str) and entry["description"]
    assert isinstance(entry["tier"], int)
    assert isinstance(entry["column"], int)
    assert isinstance(entry["dependencies"], list)
    assert isinstance(entry["resource_cost"], dict) and entry["resource_cost"]
    assert isinstance(entry["required_points"], int) and entry["required_points"] > 0
    assert isinstance(entry["image_key"], str) and entry["image_key"]


def test_technology_entries_use_static_column_and_matching_tiers() -> None:
    entries = _technology_entries()
    for index, entry in enumerate(entries, start=1):
        assert entry["tier"] == index
        assert entry["column"] == 0


def test_technology_dependency_chain() -> None:
    entries = _technology_entries()
    assert entries[0]["dependencies"] == []
    assert entries[1]["dependencies"] == ["1"]
    assert entries[2]["dependencies"] == ["2"]
    assert entries[3]["dependencies"] == ["3"]


def test_technology_ids_are_unique() -> None:
    settings = _research_settings()
    ids = [entry["id"] for entry in settings["researches"]]
    assert len(ids) == len(set(ids))
