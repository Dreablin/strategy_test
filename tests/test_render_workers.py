"""Worker render placement rules: assigned center, idle tile, orphan tile, movement."""

import pygame

import game.assets as assets
from game.buildings.field import Field
from game.buildings.lumber_camp import LumberCamp
from game.config import town_hall_origin_tile, near_town_hall_tile
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.render import Renderer
from game.world import World
from game.workers import Worker, WorkerManager, building_center_tile


def test_worker_grid_positions_assigned_worker_on_building_center() -> None:
    world = World()
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    camp = registry.place(LumberCamp, near_town_hall_tile(8, 8))
    wm = WorkerManager(registry)
    w = Worker("LUMBERJACK")
    wm.add_worker(w)
    wm.assign_to_building(w, camp)
    pos = Renderer.worker_grid_positions(registry, wm)
    assert pos == [("LUMBERJACK", building_center_tile(camp))]


def test_worker_grid_positions_idle_workers_stay_on_their_stand_tiles() -> None:
    world = World()
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    wm = WorkerManager(registry)
    wm.add_worker(Worker("LUMBERJACK", stand_tile=building_center_tile(town_hall)))
    wm.add_worker(Worker("FARMER", stand_tile=(0, 0)))
    pos = Renderer.worker_grid_positions(registry, wm)
    assert pos == [
        ("LUMBERJACK", building_center_tile(town_hall)),
        ("FARMER", (0, 0)),
    ]


def test_worker_grid_positions_orphan_stays_on_demolished_center() -> None:
    world = World()
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    camp = registry.place(LumberCamp, near_town_hall_tile(8, 8))
    wm = WorkerManager(registry)
    w = Worker("LUMBERJACK")
    wm.add_worker(w)
    wm.assign_to_building(w, camp)
    center = building_center_tile(camp)
    registry.demolish(camp, wm)
    pos = Renderer.worker_grid_positions(registry, wm)
    assert pos == [("LUMBERJACK", center)]


def test_draw_workers_moving_worker_pixel_shifts_between_frames(monkeypatch) -> None:
    world = World()
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    wm = WorkerManager(registry)
    c = near_town_hall_tile()
    w = Worker("LUMBERJACK", stand_tile=c)
    w.start_move([c, (c[0] + 1, c[1])], started_ms=0)
    wm.add_worker(w)

    dot = pygame.Surface((1, 1), pygame.SRCALPHA)
    dot.fill((255, 0, 0, 255))
    monkeypatch.setattr(assets, "worker_dot", lambda _t, carrying=False: dot)

    surface = pygame.Surface((1280, 720), pygame.SRCALPHA)
    Renderer.draw_workers(surface, world, registry, wm)
    first = surface.get_bounding_rect()

    wm.update(1500)
    surface.fill((0, 0, 0, 0))
    Renderer.draw_workers(surface, world, registry, wm)
    second = surface.get_bounding_rect()

    assert first.width == 1 and first.height == 1
    assert second.width == 1 and second.height == 1
    assert second.x > first.x


def test_draw_workers_lumberjack_going_to_tree_interpolates_between_tiles(monkeypatch) -> None:
    world = World()
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    wm = WorkerManager(registry)
    c = near_town_hall_tile()
    w = Worker("LUMBERJACK", stand_tile=c)
    w.start_move([c, (c[0] + 1, c[1])], started_ms=0, move_state="going_to_tree")
    wm.add_worker(w)

    dot = pygame.Surface((1, 1), pygame.SRCALPHA)
    dot.fill((255, 0, 0, 255))
    monkeypatch.setattr(assets, "worker_dot", lambda _t, carrying=False: dot)

    surface = pygame.Surface((1280, 720), pygame.SRCALPHA)
    Renderer.draw_workers(surface, world, registry, wm)
    first = surface.get_bounding_rect()

    wm.update(1500)
    surface.fill((0, 0, 0, 0))
    Renderer.draw_workers(surface, world, registry, wm)
    second = surface.get_bounding_rect()

    assert first.width == 1 and first.height == 1
    assert second.width == 1 and second.height == 1
    assert second.x > first.x


def test_draw_workers_lumberjack_returning_interpolates_between_tiles(monkeypatch) -> None:
    world = World()
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    wm = WorkerManager(registry)
    c = near_town_hall_tile()
    w = Worker("LUMBERJACK", stand_tile=c)
    w.carrying = "wood"
    w.start_move([c, (c[0] + 1, c[1])], started_ms=0, move_state="returning")
    wm.add_worker(w)

    dot = pygame.Surface((1, 1), pygame.SRCALPHA)
    dot.fill((255, 0, 0, 255))
    monkeypatch.setattr(assets, "worker_dot", lambda _t, carrying=False: dot)

    surface = pygame.Surface((1280, 720), pygame.SRCALPHA)
    Renderer.draw_workers(surface, world, registry, wm)
    first = surface.get_bounding_rect()

    wm.update(1500)
    surface.fill((0, 0, 0, 0))
    Renderer.draw_workers(surface, world, registry, wm)
    second = surface.get_bounding_rect()

    assert first.width == 1 and first.height == 1
    assert second.width == 1 and second.height == 1
    assert second.x > first.x


def test_draw_workers_stonecutter_going_to_stone_interpolates_between_tiles(monkeypatch) -> None:
    world = World()
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    wm = WorkerManager(registry)
    c = near_town_hall_tile()
    w = Worker("STONECUTTER", stand_tile=c)
    w.start_move([c, (c[0] + 1, c[1])], started_ms=0, move_state="going_to_stone")
    wm.add_worker(w)

    dot = pygame.Surface((1, 1), pygame.SRCALPHA)
    dot.fill((255, 0, 0, 255))
    monkeypatch.setattr(assets, "worker_dot", lambda _t, carrying=False: dot)

    surface = pygame.Surface((1280, 720), pygame.SRCALPHA)
    Renderer.draw_workers(surface, world, registry, wm)
    first = surface.get_bounding_rect()

    wm.update(1500)
    surface.fill((0, 0, 0, 0))
    Renderer.draw_workers(surface, world, registry, wm)
    second = surface.get_bounding_rect()

    assert first.width == 1 and first.height == 1
    assert second.width == 1 and second.height == 1
    assert second.x > first.x


def test_draw_workers_forester_going_to_plant_tile_interpolates_between_tiles(monkeypatch) -> None:
    world = World()
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    wm = WorkerManager(registry)
    c = near_town_hall_tile()
    w = Worker("FORESTER", stand_tile=c)
    w.start_move([c, (c[0] + 1, c[1])], started_ms=0, move_state="going_to_plant_tile")
    wm.add_worker(w)

    dot = pygame.Surface((1, 1), pygame.SRCALPHA)
    dot.fill((255, 0, 0, 255))
    monkeypatch.setattr(assets, "worker_dot", lambda _t, carrying=False: dot)

    surface = pygame.Surface((1280, 720), pygame.SRCALPHA)
    Renderer.draw_workers(surface, world, registry, wm)
    first = surface.get_bounding_rect()

    wm.update(1500)
    surface.fill((0, 0, 0, 0))
    Renderer.draw_workers(surface, world, registry, wm)
    second = surface.get_bounding_rect()

    assert first.width == 1 and first.height == 1
    assert second.width == 1 and second.height == 1
    assert second.x > first.x


def test_draw_workers_uses_carrying_variant_for_lumberjack(monkeypatch) -> None:
    world = World()
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    wm = WorkerManager(registry)
    w = Worker("LUMBERJACK", stand_tile=near_town_hall_tile())
    w.carrying = "wood"
    wm.add_worker(w)

    calls: list[bool] = []
    dot = pygame.Surface((1, 1), pygame.SRCALPHA)
    dot.fill((255, 0, 0, 255))

    def fake_worker_dot(_t: str, carrying: bool = False) -> pygame.Surface:
        calls.append(carrying)
        return dot

    monkeypatch.setattr(assets, "worker_dot", fake_worker_dot)
    surface = pygame.Surface((1280, 720), pygame.SRCALPHA)
    Renderer.draw_workers(surface, world, registry, wm)
    assert calls == [True]


def test_draw_workers_uses_carrying_variant_for_stonecutter(monkeypatch) -> None:
    world = World()
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    wm = WorkerManager(registry)
    w = Worker("STONECUTTER", stand_tile=near_town_hall_tile())
    w.carrying = "stone"
    wm.add_worker(w)

    calls: list[bool] = []
    dot = pygame.Surface((1, 1), pygame.SRCALPHA)
    dot.fill((255, 0, 0, 255))

    def fake_worker_dot(_t: str, carrying: bool = False) -> pygame.Surface:
        calls.append(carrying)
        return dot

    monkeypatch.setattr(assets, "worker_dot", fake_worker_dot)
    surface = pygame.Surface((1280, 720), pygame.SRCALPHA)
    Renderer.draw_workers(surface, world, registry, wm)
    assert calls == [True]


def test_draw_workers_field_build_progress_bar_only_during_active_field_build(monkeypatch) -> None:
    now_ms = {"t": 0}
    world = World(world_seed=0)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    field = registry.place(Field, near_town_hall_tile(8, 8))
    wm = WorkerManager(registry, now_ms_fn=lambda: now_ms["t"])
    builder = wm.hire("BUILDER")
    assert builder is not None

    # Make worker dot transparent so any drawn pixels come from progress bar.
    dot = pygame.Surface((1, 1), pygame.SRCALPHA)
    dot.fill((0, 0, 0, 0))
    monkeypatch.setattr(assets, "worker_dot", lambda _t, carrying=False: dot)

    # Advance until field build starts with assigned builder.
    started = False
    for _ in range(3000):
        now_ms["t"] += 500
        wm.reassign_all()
        wm.update(now_ms["t"])
        site = field.construction_site
        if site is not None and site.builder is builder and site.is_building():
            started = True
            break
    assert started

    surface = pygame.Surface((1280, 720), pygame.SRCALPHA)
    surface.fill((0, 0, 0, 0))
    Renderer.draw_workers(surface, world, registry, wm)
    assert surface.get_bounding_rect().width > 0

    # After build completes, no field build progress bar should be drawn.
    assert field.construction_site is not None
    complete_at = int(field.construction_site.build_started_ms) + int(field.construction_site.build_time_ms)
    now_ms["t"] = complete_at
    wm.update(now_ms["t"])

    surface.fill((0, 0, 0, 0))
    Renderer.draw_workers(surface, world, registry, wm)
    assert surface.get_bounding_rect().width == 0


def test_draw_workers_farmer_action_progress_bar_visible_during_sow_and_harvest(monkeypatch) -> None:
    world = World(world_seed=0)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    field = registry.place(Field, near_town_hall_tile(8, 8))
    field.construction_site = None

    now_ms = {"t": 5_000}
    wm = WorkerManager(registry, now_ms_fn=lambda: now_ms["t"])
    farmer = Worker("FARMER", stand_tile=field.grid_pos)
    farmer.assigned_building = registry.place(LumberCamp, near_town_hall_tile(12, 8))
    farmer.current_tile = field.grid_pos
    farmer.chop_started_ms = 0
    farmer.chop_duration_ms = 10_000
    wm.add_worker(farmer)

    dot = pygame.Surface((1, 1), pygame.SRCALPHA)
    dot.fill((0, 0, 0, 0))
    monkeypatch.setattr(assets, "worker_dot", lambda _t, carrying=False: dot)

    surface = pygame.Surface((1280, 720), pygame.SRCALPHA)
    surface.fill((0, 0, 0, 0))
    farmer.state = "sowing"
    Renderer.draw_workers(surface, world, registry, wm)
    sow_rect = surface.get_bounding_rect()
    assert sow_rect.width > 0

    surface.fill((0, 0, 0, 0))
    farmer.state = "harvesting"
    Renderer.draw_workers(surface, world, registry, wm)
    harvest_rect = surface.get_bounding_rect()
    assert harvest_rect.width > 0

    surface.fill((0, 0, 0, 0))
    farmer.state = "resting"
    Renderer.draw_workers(surface, world, registry, wm)
    assert surface.get_bounding_rect().width == 0
