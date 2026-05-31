"""Pytest configuration for headless pygame test execution."""

from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager

os.environ["SDL_VIDEODRIVER"] = "dummy"

import pygame
import pytest

from game import i18n


@pytest.fixture(scope="session", autouse=True)
def pygame_initialized():
    """Initialize and clean up pygame exactly once per test session."""
    pygame.init()
    try:
        yield
    finally:
        pygame.quit()


@contextmanager
def _use_locale(code: str) -> Iterator[None]:
    """Switch locale for a test block and restore the previous locale on exit."""
    previous = i18n.get_locale()
    i18n.set_locale(code)
    try:
        yield
    finally:
        i18n.set_locale(previous)


@pytest.fixture
def use_locale():
    """Context manager factory for temporary locale switches in tests."""
    return _use_locale


@pytest.fixture(autouse=True)
def _reset_i18n_locale_after_test() -> Iterator[None]:
    """Prevent locale state from leaking between tests."""
    yield
    i18n.set_locale("en")
