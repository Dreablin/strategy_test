"""Failing Phase 13 perf-gate smoke test (T143)."""

from __future__ import annotations

import importlib

import pygame


def test_phase13_perf_gate_regression(monkeypatch) -> None:
    import game.config as config_mod

    original_grid_size = config_mod.GRID_SIZE
    monkeypatch.setattr(config_mod, "GRID_SIZE", 100)

    import game.pathfinding as path_mod
    import game.render as render_mod
    import game.workers as workers_mod
    import game.world as world_mod

    try:
        world_mod = importlib.reload(world_mod)
        path_mod = importlib.reload(path_mod)
        workers_mod = importlib.reload(workers_mod)
        render_mod = importlib.reload(render_mod)

        from game.buildings.lumber_camp import LumberCamp
        from game.buildings.registry import BuildingRegistry
        from game.buildings.stone_mine import StoneMine
        from game.buildings.town_hall import TownHall
        
        world = world_mod.World()
        world._trees.clear()  # noqa: SLF001
        world._stones.clear()  # noqa: SLF001
        world._iron.clear()  # noqa: SLF001
        world._gold.clear()  # noqa: SLF001

        registry = BuildingRegistry(world)
        town_hall = registry.place(TownHall, (48, 48))
        town_hall.level = 5

        lumber_positions = [(8, 8), (8, 24), (8, 40), (24, 8), (24, 24)]
        mine_positions = [(60, 8), (60, 24), (60, 40), (76, 8), (76, 24)]
        camps = [registry.place(LumberCamp, pos) for pos in lumber_positions]
        mines = [registry.place(StoneMine, pos) for pos in mine_positions]
        assert len(camps) == 5
        assert len(mines) == 5
        for building in [*camps, *mines]:
            gx, gy = building.grid_pos  # type: ignore[misc]
            w = type(building).footprint[0]
            h = type(building).footprint[1]
            for y in range(gy - 1, gy + h + 1):
                for x in range(gx - 1, gx + w + 1):
                    if gx <= x < gx + w and gy <= y < gy + h:
                        continue
                    if world.is_in_grass(x, y):
                        world.mark_occupied(x, y, 1, 1)

        now_ms = {"t": 0}
        manager = workers_mod.WorkerManager(registry, now_ms_fn=lambda: now_ms["t"])

        for _ in range(5):
            assert manager.hire("LUMBERJACK") is not None
            assert manager.hire("STONECUTTER") is not None

        counters = {"path": 0, "occupied": 0, "screen": 0}
        real_path = workers_mod.find_path_to_any_bfs
        real_occupied = world_mod.World.is_occupied
        real_screen = render_mod.world_to_screen

        def counted_path(*args, **kwargs):  # noqa: ANN002, ANN003
            counters["path"] += 1
            return real_path(*args, **kwargs)

        def counted_occupied(self, gx: int, gy: int):  # noqa: ANN001
            counters["occupied"] += 1
            return real_occupied(self, gx, gy)

        def counted_screen(gx: int, gy: int):
            counters["screen"] += 1
            return real_screen(gx, gy)

        monkeypatch.setattr(workers_mod, "find_path_to_any_bfs", counted_path)
        monkeypatch.setattr(world_mod.World, "is_occupied", counted_occupied)
        monkeypatch.setattr(render_mod, "world_to_screen", counted_screen)

        for _ in range(100):
            now_ms["t"] += 16
            manager.reassign_all()
            manager.update(now_ms["t"])

        surface = pygame.Surface((800, 600))
        render_mod.Renderer.draw_world(surface, world)
        render_mod.Renderer.draw_buildings(surface, world, registry)
        render_mod.Renderer.draw_workers(surface, world, registry, manager)
        render_mod.Renderer.draw_trees(surface, world)
        render_mod.Renderer.draw_stones(surface, world)

        assert counters["path"] <= 250
        assert counters["occupied"] <= 6_000
        assert counters["screen"] <= 4_000
    finally:
        monkeypatch.setattr(config_mod, "GRID_SIZE", original_grid_size)
        importlib.reload(world_mod)
        importlib.reload(path_mod)
        importlib.reload(workers_mod)
        importlib.reload(render_mod)
