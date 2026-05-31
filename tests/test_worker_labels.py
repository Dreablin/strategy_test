"""Parametrized worker display label tests (T446)."""

from __future__ import annotations

import pytest

from game.ui.worker_labels import worker_display_label
from game.worker_hiring import HIRABLE_WORKERS

_EN_LABELS: dict[str, str] = {
    "ANIMAL_HERDER": "Herder",
    "BAKER": "Baker",
    "BUILDER": "Builder",
    "CARRIER": "Carrier",
    "COOK": "Cook",
    "FARMER": "Farmer",
    "FORESTER": "Forester",
    "LUMBERJACK": "Lumberjack",
    "MILLER": "Miller",
    "MINER": "Miner",
    "SAWYER": "Sawyer",
    "SCIENTIST": "Scientist",
    "STONECUTTER": "Stonecutter",
    "WATERMAN": "Waterman",
    "WINEMAKER": "Winemaker",
}

_RU_LABELS: dict[str, str] = {
    "ANIMAL_HERDER": "Пастух",
    "BAKER": "Пекарь",
    "BUILDER": "Строитель",
    "CARRIER": "Переносчик",
    "COOK": "Повар",
    "FARMER": "Фермер",
    "FORESTER": "Лесничий",
    "LUMBERJACK": "Лесоруб",
    "MILLER": "Мельник",
    "MINER": "Шахтёр",
    "SAWYER": "Пильщик",
    "SCIENTIST": "Учёный",
    "STONECUTTER": "Каменщик",
    "WATERMAN": "Водонос",
    "WINEMAKER": "Винодел",
}


@pytest.mark.parametrize("worker_type", sorted(HIRABLE_WORKERS))
def test_worker_display_label_en(worker_type: str) -> None:
    assert worker_display_label(worker_type) == _EN_LABELS[worker_type]


@pytest.mark.parametrize("worker_type", sorted(HIRABLE_WORKERS))
def test_worker_display_label_ru(worker_type: str, use_locale) -> None:
    with use_locale("ru"):
        assert worker_display_label(worker_type) == _RU_LABELS[worker_type]
