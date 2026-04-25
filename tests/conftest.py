"""Pytest configuration for headless pygame test execution."""

import os

os.environ["SDL_VIDEODRIVER"] = "dummy"

import pygame
import pytest


@pytest.fixture(scope="session", autouse=True)
def pygame_initialized():
    """Initialize and clean up pygame exactly once per test session."""
    pygame.init()
    try:
        yield
    finally:
        pygame.quit()
