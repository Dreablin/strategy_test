"""Research definitions loaded and validated from ``settings/research.json``."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

_MIN_TIER = 1
_MAX_TIER = 4


@dataclass(frozen=True, slots=True)
class ResearchDefinition:
    id: str
    name: str
    description: str
    tier: int
    column: int
    dependencies: tuple[str, ...]
    resource_cost: dict[str, int]
    required_points: int
    image_key: str


def _settings_path() -> Path:
    return Path(__file__).resolve().parent / "settings" / "research.json"


def _load_json_object(path: Path) -> dict:
    try:
        loaded = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}") from exc
    if not isinstance(loaded, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    return loaded


def _parse_resource_cost(raw: object, *, research_id: str) -> dict[str, int]:
    if not isinstance(raw, dict) or not raw:
        raise ValueError(f"research {research_id!r}: resource_cost must be a non-empty object")
    cost: dict[str, int] = {}
    for resource, amount in raw.items():
        key = str(resource).strip()
        if not key:
            raise ValueError(f"research {research_id!r}: resource_cost keys must be non-empty")
        if not isinstance(amount, int) or isinstance(amount, bool):
            raise ValueError(
                f"research {research_id!r}: resource_cost[{key!r}] must be a positive integer"
            )
        if amount <= 0:
            raise ValueError(
                f"research {research_id!r}: resource_cost[{key!r}] must be a positive integer"
            )
        cost[key] = amount
    return cost


def _parse_dependencies(raw: object, *, research_id: str) -> tuple[str, ...]:
    if not isinstance(raw, list):
        raise ValueError(f"research {research_id!r}: dependencies must be a list")
    deps: list[str] = []
    for item in raw:
        dep_id = str(item).strip()
        if not dep_id:
            raise ValueError(f"research {research_id!r}: dependency ids must be non-empty")
        if dep_id == research_id:
            raise ValueError(f"research {research_id!r}: cannot depend on itself")
        deps.append(dep_id)
    return tuple(deps)


def _parse_entry(raw: object) -> ResearchDefinition:
    if not isinstance(raw, dict):
        raise ValueError("each research entry must be an object")
    research_id = str(raw.get("id", "")).strip()
    if not research_id:
        raise ValueError("research id must be a non-empty string")

    name = raw.get("name")
    description = raw.get("description")
    if not isinstance(name, str) or not name.strip():
        raise ValueError(f"research {research_id!r}: name must be a non-empty string")
    if not isinstance(description, str) or not description.strip():
        raise ValueError(f"research {research_id!r}: description must be a non-empty string")

    tier = raw.get("tier")
    if not isinstance(tier, int) or isinstance(tier, bool):
        raise ValueError(f"research {research_id!r}: tier must be an integer")
    if tier < _MIN_TIER or tier > _MAX_TIER:
        raise ValueError(
            f"research {research_id!r}: tier must be in [{_MIN_TIER}, {_MAX_TIER}], got {tier}"
        )

    column = raw.get("column")
    if not isinstance(column, int) or isinstance(column, bool):
        raise ValueError(f"research {research_id!r}: column must be an integer")
    if column < 0:
        raise ValueError(f"research {research_id!r}: column must be non-negative")

    image_key = raw.get("image_key")
    if not isinstance(image_key, str) or not image_key.strip():
        raise ValueError(f"research {research_id!r}: image_key must be a non-empty string")

    required_points = raw.get("required_points")
    if not isinstance(required_points, int) or isinstance(required_points, bool):
        raise ValueError(f"research {research_id!r}: required_points must be a positive integer")
    if required_points <= 0:
        raise ValueError(f"research {research_id!r}: required_points must be a positive integer")

    return ResearchDefinition(
        id=research_id,
        name=name.strip(),
        description=description.strip(),
        tier=tier,
        column=column,
        dependencies=_parse_dependencies(raw.get("dependencies"), research_id=research_id),
        resource_cost=_parse_resource_cost(raw.get("resource_cost"), research_id=research_id),
        required_points=required_points,
        image_key=image_key.strip(),
    )


def _validate_dependency_references(definitions: tuple[ResearchDefinition, ...]) -> None:
    known_ids = {entry.id for entry in definitions}
    for entry in definitions:
        for dep_id in entry.dependencies:
            if dep_id not in known_ids:
                raise ValueError(
                    f"research {entry.id!r}: unknown dependency {dep_id!r}"
                )


def load_research_definitions(path: Path | None = None) -> tuple[ResearchDefinition, ...]:
    """Load and validate research definitions from JSON."""
    settings_path = path if path is not None else _settings_path()
    if not settings_path.exists():
        raise FileNotFoundError(f"Missing required settings file: {settings_path}")

    payload = _load_json_object(settings_path)
    raw_entries = payload.get("researches")
    if not isinstance(raw_entries, list) or not raw_entries:
        raise ValueError("researches must be a non-empty list")

    definitions = tuple(_parse_entry(entry) for entry in raw_entries)
    seen: set[str] = set()
    for entry in definitions:
        if entry.id in seen:
            raise ValueError(f"duplicate research id {entry.id!r}")
        seen.add(entry.id)

    _validate_dependency_references(definitions)
    return definitions


RESEARCH_DEFINITIONS: tuple[ResearchDefinition, ...] = load_research_definitions()
RESEARCH_BY_ID: dict[str, ResearchDefinition] = {entry.id: entry for entry in RESEARCH_DEFINITIONS}
