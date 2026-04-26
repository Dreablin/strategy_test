"""RMB drag threshold behavior for camera pan vs cancel."""

import pygame

from game.buildings.registry import BuildingRegistry
from game.input import GameInput
from game.resources import ResourceManager
from game.ui.bottom_bar import BUILD_MENU_SELECT
from game.ui.placement import PlacementController
from game.world import World
from game.workers import WorkerManager


class _StubCamera:
    def __init__(self) -> None:
        self.offset = (0, 0)
        self.pan_calls: list[tuple[int, int]] = []
        self.clamp_calls = 0

    def pan(self, dx: int, dy: int) -> None:
        self.pan_calls.append((dx, dy))
        self.offset = (self.offset[0] + dx, self.offset[1] + dy)

    def clamp(self, viewport_size: tuple[int, int], world_bounds_px: tuple[int, int, int, int]) -> None:
        _ = (viewport_size, world_bounds_px)
        self.clamp_calls += 1


def _setup() -> tuple[pygame.Surface, GameInput, PlacementController, _StubCamera]:
    surface = pygame.Surface((1280, 720))
    world = World()
    registry = BuildingRegistry(world)
    resources = ResourceManager()
    camera = _StubCamera()
    placement = PlacementController(world, registry, resources, camera)
    workers = WorkerManager(resources, registry)
    gi = GameInput(world, registry, resources, placement, workers, camera)
    gi.handle(surface, pygame.event.Event(BUILD_MENU_SELECT, building_type="LUMBER_CAMP"))
    return surface, gi, placement, camera


def test_rmb_drag_below_threshold_triggers_cancel_on_release() -> None:
    surface, gi, placement, camera = _setup()
    gi.handle(surface, pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=pygame.BUTTON_RIGHT, pos=(400, 300)))
    gi.handle(
        surface,
        pygame.event.Event(pygame.MOUSEMOTION, pos=(403, 300), rel=(3, 0), buttons=(0, 0, 1)),
    )
    gi.handle(surface, pygame.event.Event(pygame.MOUSEBUTTONUP, button=pygame.BUTTON_RIGHT, pos=(403, 300)))
    assert placement.pending_type is None
    assert camera.pan_calls == []
    assert camera.clamp_calls == 0


def test_rmb_drag_above_threshold_pans_and_does_not_cancel() -> None:
    surface, gi, placement, camera = _setup()
    gi.handle(surface, pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=pygame.BUTTON_RIGHT, pos=(400, 300)))
    gi.handle(
        surface,
        pygame.event.Event(pygame.MOUSEMOTION, pos=(405, 300), rel=(5, 0), buttons=(0, 0, 1)),
    )
    assert gi.consume_camera_moved() is True
    gi.handle(surface, pygame.event.Event(pygame.MOUSEBUTTONUP, button=pygame.BUTTON_RIGHT, pos=(405, 300)))
    assert placement.pending_type is not None
    assert camera.pan_calls == [(5, 0)]
    assert camera.clamp_calls == 0
