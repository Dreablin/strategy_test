"""Rendering tests for iron world deposits."""

import pygame

from game.config import GRID_SIZE, TILE_H, TILE_W
from game.iron import IronDeposit
from game.iso import world_to_screen
from game.render import Renderer
from game.world import World


def test_renderer_has_draw_iron_callable() -> None:
    assert callable(getattr(Renderer, "draw_iron", None))


def test_draw_iron_blits_bottom_center_anchor(monkeypatch) -> None:
    world = World()
    world._iron.clear()  # noqa: SLF001
    cx = cy = GRID_SIZE // 2
    world._iron[(cx, cy)] = IronDeposit(blocking=True, variant=3)  # noqa: SLF001
    surface = pygame.Surface((800, 600), pygame.SRCALPHA)
    sprite = pygame.Surface((20, 10), pygame.SRCALPHA)
    sprite.fill((200, 100, 80, 255))
    calls: list[tuple[int, bool]] = []

    def fake_sprite(variant: int = 0, *, blocking: bool = False) -> pygame.Surface:
        calls.append((variant, blocking))
        return sprite

    monkeypatch.setattr("game.render.iron_sprite", fake_sprite)
    monkeypatch.setattr("game.render.iron_sprite_anchor", lambda _variant, *, blocking=False: (10, 10))
    monkeypatch.setattr("game.render.iron_sprite_offset", lambda _variant, *, blocking=False: (0, 0))

    Renderer.draw_world(surface, world)
    Renderer.draw_iron(surface, world, camera=None)

    ox, oy = Renderer.map_origin(surface, world)
    sx, sy = world_to_screen(cx, cy)
    expected_x = ox + sx + TILE_W // 2 - 10
    expected_y = oy + sy + TILE_H - 10
    assert calls == [(3, True)]
    assert surface.get_at((expected_x + 10, expected_y + 5)).a == 255
