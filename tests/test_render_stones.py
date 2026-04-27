"""Failing render tests for stone sprites and layering (T114)."""

import pygame

import game.render as render_mod
from game.camera import Camera
from game.iso import world_to_screen
from game.render import Renderer
from game.stones import Stone
from game.world import World

_BG = (17, 19, 23)


def test_world_iter_stones_returns_all_entries() -> None:
    world = World()
    world._stones = {(4, 5): Stone(), (8, 9): Stone()}  # noqa: SLF001
    entries = world.iter_stones()
    assert len(entries) == 2
    assert ((4, 5), world.stone_at(4, 5)) in entries
    assert ((8, 9), world.stone_at(8, 9)) in entries


def test_renderer_has_draw_stones_callable() -> None:
    assert callable(getattr(Renderer, "draw_stones", None))


def test_draw_stones_blits_bottom_center_anchor(monkeypatch) -> None:
    world = World()
    world._stones = {(27, 27): Stone()}  # noqa: SLF001
    sprite = pygame.Surface((1, 1), pygame.SRCALPHA)
    sprite.fill((0, 255, 255, 255))
    monkeypatch.setattr(render_mod, "stone_sprite", lambda: sprite, raising=False)

    surface = pygame.Surface((1280, 720), pygame.SRCALPHA)
    surface.fill(_BG)
    Renderer.draw_world(surface, world)
    Renderer.draw_stones(surface, world, camera=None)

    ox, oy = Renderer.map_origin(surface, world)
    sx, sy = world_to_screen(27, 27)
    px = ox + sx + 32
    py = oy + sy + 31
    assert surface.get_at((px, py))[:3] == (0, 255, 255)


def test_draw_stones_respects_camera_offset(monkeypatch) -> None:
    world = World()
    world._stones = {(27, 27): Stone()}  # noqa: SLF001
    sprite = pygame.Surface((1, 1), pygame.SRCALPHA)
    sprite.fill((255, 0, 255, 255))
    monkeypatch.setattr(render_mod, "stone_sprite", lambda: sprite, raising=False)

    camera = Camera(initial_offset=(50, 30))
    surface = pygame.Surface((1280, 720), pygame.SRCALPHA)
    surface.fill(_BG)
    Renderer.draw_world(surface, world, camera=camera)
    Renderer.draw_stones(surface, world, camera=camera)

    ox, oy = Renderer.map_origin(surface, world)
    sx, sy = world_to_screen(27, 27)
    px = ox + camera.offset[0] + sx + 32
    py = oy + camera.offset[1] + sy + 31
    assert surface.get_at((px, py))[:3] == (255, 0, 255)


def test_draw_stones_uses_procedural_fallback_when_asset_missing(monkeypatch) -> None:
    world = World()
    world._stones = {(10, 10): Stone()}  # noqa: SLF001
    calls: list[str] = []

    def _fake_sprite() -> pygame.Surface:
        calls.append("called")
        surf = pygame.Surface((1, 1), pygame.SRCALPHA)
        surf.fill((255, 255, 0, 255))
        return surf

    monkeypatch.setattr(render_mod, "stone_sprite", _fake_sprite, raising=False)
    surface = pygame.Surface((1280, 720), pygame.SRCALPHA)
    surface.fill(_BG)
    Renderer.draw_world(surface, world)
    Renderer.draw_stones(surface, world)
    assert calls == ["called"]
