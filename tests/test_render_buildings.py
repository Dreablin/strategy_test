"""Failing tests for Renderer.draw_buildings (Phase 8 T43)."""

from __future__ import annotations

import pygame

from game.construction import ConstructionSite
from game.assets import grass_tile
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.buildings.field import Field, WHEAT_EMPTY, WHEAT_PHASE_3
from game.buildings.lumber_camp import LumberCamp
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.camera import Camera
from game.iso import world_to_screen
from game.render import Renderer
import game.render as render_mod
from game.world import World
from game.workers import WorkerManager

_SENTINEL = (20, 24, 22)


def _tile_center_pixel(surface: pygame.Surface, world: World, gx: int, gy: int) -> tuple[int, int]:
    ox, oy = Renderer.map_origin(surface, world)
    sx, sy = world_to_screen(gx, gy)
    return ox + sx + 32, oy + sy + 16


def test_draw_buildings_attribute() -> None:
    assert callable(getattr(Renderer, "draw_buildings", None))


def test_initial_town_hall_drawn() -> None:
    world = World()
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    surface = pygame.Surface((1280, 720))
    surface.fill(_SENTINEL)
    Renderer.draw_world(surface, world)
    Renderer.draw_buildings(surface, world, registry)

    thx, thy = town_hall_origin_tile()
    px, py = _tile_center_pixel(surface, world, thx + 1, thy + 1)
    color = surface.get_at((px, py))[:3]
    grass_color = grass_tile().get_at((32, 16))[:3]
    assert color != _SENTINEL
    assert color != grass_color


def test_placed_building_drawn() -> None:
    world = World()
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    camp = registry.place(LumberCamp, near_town_hall_tile(8, 8))
    surface = pygame.Surface((1280, 720))
    surface.fill(_SENTINEL)
    Renderer.draw_world(surface, world)
    Renderer.draw_buildings(surface, world, registry)

    cx, cy = camp.grid_pos  # type: ignore[assignment]
    px, py = _tile_center_pixel(surface, world, cx + 1, cy + 1)
    color = surface.get_at((px, py))[:3]
    grass_color = grass_tile().get_at((32, 16))[:3]
    assert color != _SENTINEL
    assert color != grass_color


class _Spy:
    """Surface wrapper that records `blit` calls."""

    def __init__(self, inner: pygame.Surface) -> None:
        self.inner = inner
        self.calls: list[tuple[tuple, dict]] = []

    def blit(self, *args, **kwargs):  # noqa: ANN002, ANN003
        self.calls.append((args, kwargs))
        return self.inner.blit(*args, **kwargs)

    def __getattr__(self, name: str):
        return getattr(self.inner, name)


def test_painters_order() -> None:
    world = World()
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    registry.place(LumberCamp, near_town_hall_tile(8, 8))
    registry.place(LumberCamp, near_town_hall_tile(15, 15))
    spy = _Spy(pygame.Surface((1280, 720)))
    Renderer.draw_buildings(spy, world, registry)

    # Building blits should follow painter's order by grid depth.
    dests = [args[1] for args, _kwargs in spy.calls if len(args) >= 2]
    assert len(dests) >= 3
    # First camp (smaller gx+gy), then town hall, then second camp.
    assert dests[0][1] < dests[2][1]


def test_draw_building_shifted_by_camera_offset() -> None:
    world = World()
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    camp = registry.place(LumberCamp, near_town_hall_tile(8, 8))

    no_cam = pygame.Surface((1280, 720))
    no_cam.fill(_SENTINEL)
    Renderer.draw_world(no_cam, world, None)
    Renderer.draw_buildings(no_cam, world, registry, None)

    with_cam = pygame.Surface((1280, 720))
    with_cam.fill(_SENTINEL)
    camera = Camera((50, 30))
    Renderer.draw_world(with_cam, world, camera)
    Renderer.draw_buildings(with_cam, world, registry, camera)

    cx, cy = camp.grid_pos  # type: ignore[assignment]
    px, py = _tile_center_pixel(no_cam, world, cx + 1, cy + 1)
    px2, py2 = px + 50, py + 30
    assert no_cam.get_at((px, py))[:3] != _SENTINEL
    assert with_cam.get_at((px2, py2))[:3] != _SENTINEL


def test_draw_buildings_uses_construction_sprite_for_under_construction(monkeypatch) -> None:
    world = World()
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    camp = registry.place(LumberCamp, near_town_hall_tile(8, 8))
    camp.construction_site = ConstructionSite(
        required_resources={"wood": 2},
        delivered_resources={},
        build_time_ms=10_000,
        build_started_ms=None,
        builder=None,
        target_level=3,
    )
    surface = pygame.Surface((1280, 720))
    construction_calls: list[tuple[str, int]] = []
    normal_calls: list[tuple[str, int]] = []

    def _construction_sprite(b_type: str, level: int) -> pygame.Surface:
        construction_calls.append((b_type, level))
        return pygame.Surface((16, 16), pygame.SRCALPHA)

    def _normal_sprite(b_type: str, level: int) -> pygame.Surface:
        normal_calls.append((b_type, level))
        return pygame.Surface((16, 16), pygame.SRCALPHA)

    monkeypatch.setattr(render_mod, "building_sprite_construction", _construction_sprite)
    monkeypatch.setattr(render_mod, "building_sprite", _normal_sprite)
    monkeypatch.setattr(render_mod, "building_sprite_anchor", lambda _t, _l: (8, 16))

    Renderer.draw_buildings(surface, world, registry)

    assert ("LUMBER_CAMP", 3) in construction_calls
    assert ("LUMBER_CAMP", camp.level) not in normal_calls


def test_draw_buildings_uses_normal_sprite_for_completed_building(monkeypatch) -> None:
    world = World()
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    camp = registry.place(LumberCamp, near_town_hall_tile(8, 8))
    camp.construction_site = None
    surface = pygame.Surface((1280, 720))
    construction_calls: list[tuple[str, int]] = []
    normal_calls: list[tuple[str, int]] = []

    def _construction_sprite(b_type: str, level: int) -> pygame.Surface:
        construction_calls.append((b_type, level))
        return pygame.Surface((16, 16), pygame.SRCALPHA)

    def _normal_sprite(b_type: str, level: int) -> pygame.Surface:
        normal_calls.append((b_type, level))
        return pygame.Surface((16, 16), pygame.SRCALPHA)

    monkeypatch.setattr(render_mod, "building_sprite_construction", _construction_sprite)
    monkeypatch.setattr(render_mod, "building_sprite", _normal_sprite)
    monkeypatch.setattr(render_mod, "building_sprite_anchor", lambda _t, _l: (8, 16))

    Renderer.draw_buildings(surface, world, registry)

    assert ("LUMBER_CAMP", camp.level) in normal_calls
    assert not any(call[0] == "LUMBER_CAMP" for call in construction_calls)


def test_draw_buildings_uses_phase_specific_field_sprite_level(monkeypatch) -> None:
    world = World()
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    field = registry.place(Field, near_town_hall_tile(8, 8))
    field.construction_site = None
    worker_manager = WorkerManager(registry, now_ms_fn=lambda: 0)
    worker_manager._write_field_phase(field, WHEAT_PHASE_3)  # noqa: SLF001
    surface = pygame.Surface((1280, 720))
    normal_calls: list[tuple[str, int]] = []

    def _normal_sprite(b_type: str, level: int) -> pygame.Surface:
        normal_calls.append((b_type, level))
        return pygame.Surface((16, 16), pygame.SRCALPHA)

    monkeypatch.setattr(render_mod, "building_sprite", _normal_sprite)
    monkeypatch.setattr(render_mod, "building_sprite_anchor", lambda _t, _l: (8, 16))

    Renderer.draw_buildings(surface, world, registry, worker_manager)

    assert ("FIELD", 3) in normal_calls


def test_draw_buildings_uses_empty_field_sprite_level(monkeypatch) -> None:
    world = World()
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    field = registry.place(Field, near_town_hall_tile(8, 8))
    field.construction_site = None
    worker_manager = WorkerManager(registry, now_ms_fn=lambda: 0)
    worker_manager._write_field_phase(field, WHEAT_EMPTY)  # noqa: SLF001
    surface = pygame.Surface((1280, 720))
    normal_calls: list[tuple[str, int]] = []

    def _normal_sprite(b_type: str, level: int) -> pygame.Surface:
        normal_calls.append((b_type, level))
        return pygame.Surface((16, 16), pygame.SRCALPHA)

    monkeypatch.setattr(render_mod, "building_sprite", _normal_sprite)
    monkeypatch.setattr(render_mod, "building_sprite_anchor", lambda _t, _l: (8, 16))

    Renderer.draw_buildings(surface, world, registry, worker_manager)

    assert ("FIELD", 0) in normal_calls
