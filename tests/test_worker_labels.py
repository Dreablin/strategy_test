"""Parametrized worker display label tests (T446)."""

from __future__ import annotations

import pytest

from game import i18n
from game.ui.worker_labels import worker_display_label
from game.worker_hiring import HIRABLE_WORKERS


@pytest.mark.parametrize("worker_type", sorted(HIRABLE_WORKERS))
def test_worker_display_label_en(worker_type: str) -> None:
    assert worker_display_label(worker_type) == i18n.t(f"worker.{worker_type}")


@pytest.mark.parametrize("worker_type", sorted(HIRABLE_WORKERS))
def test_worker_display_label_ru(worker_type: str, use_locale) -> None:
    with use_locale("ru"):
        assert worker_display_label(worker_type) == i18n.t(f"worker.{worker_type}")
