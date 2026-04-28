"""Phase 14 end-to-end smoke: forester planting, maturation, chop, and render."""

from __future__ import annotations

import pygame

from game.buildings.forester_hut import ForesterHut
from game.buildings.lumber_camp import LumberCamp
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.render import Renderer
from game.resources import ResourceManager
from game.trees import TreeStage
from game.world import World
from game.workers import WorkerManager


def test_smoke_phase14_forestry_cycle_to_render() -> None:
    now_ms = {"t": 0}
    world = World(world_seed=0)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001

    resources = ResourceManager()
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    town_hall.level = 10
    forester_hut = registry.place(ForesterHut, near_town_hall_tile(12, 4))
    lumber_camp = registry.place(LumberCamp, near_town_hall_tile(4, 12))

    workers = WorkerManager(resources, registry, now_ms_fn=lambda: now_ms["t"])
    assert workers.hire("FORESTER") is not None
    assert workers.hire("LUMBERJACK") is not None

    planted_tile: tuple[int, int] | None = None
    for _ in range(1200):
        now_ms["t"] += 500
        workers.reassign_all()
        workers.update(now_ms["t"])
        planted = [(pos, tree) for pos, tree in world.iter_alive_trees() if tree.stage == TreeStage.SAPLING]
        if planted:
            planted_tile = planted[0][0]
            break
    assert planted_tile is not None

    # Growth should advance during regular runtime updates (no explicit test-side growth call).
    matured = False
    for _ in range(1200):
        now_ms["t"] += 500
        workers.reassign_all()
        workers.update(now_ms["t"])
        tree = world.tree_at(*planted_tile)
        if tree is not None and tree.stage == TreeStage.ADULT:
            matured = True
            break
    assert matured, "expected planted tree to mature during runtime updates"
    # Freeze reforestation so lumberjack has one mature planted target to clear.
    forester_hut.set_active(False)
    wood_before = resources.get("wood")

    chopped = False
    for _ in range(1200):
        now_ms["t"] += 500
        workers.reassign_all()
        workers.update(now_ms["t"])
        # Forester picks random valid tiles; validate that lumberjack eventually harvests wood,
        # not strictly that this exact planted tile is the one chopped first.
        if resources.get("wood") > wood_before:
            chopped = True
            break
    assert chopped, "expected lumberjack to eventually harvest at least one matured planted tree"

    # Render one frame with mixed tree species present; no exceptions and non-bg pixels.
    planted_species: set[int] = set()
    for species in (0, 1, 2):
        planted = False
        for y in range(56, 66):
            for x in range(56, 66):
                if world.plant_tree(x, y, now_ms=now_ms["t"], species=species) is not None:
                    planted = True
                    planted_species.add(species)
                    break
            if planted:
                break
        assert planted, f"expected at least one free tile for species={species}"
    assert planted_species == {0, 1, 2}

    surface = pygame.Surface((320, 240), pygame.SRCALPHA)
    bg = (20, 24, 22, 255)
    surface.fill(bg)
    Renderer.draw_world(surface, world)
    Renderer.draw_buildings(surface, world, registry)
    Renderer.draw_workers(surface, world, registry, workers)
    Renderer.draw_trees(surface, world)
    Renderer.draw_stones(surface, world)

    has_non_bg = any(surface.get_at((x, y)) != bg for y in range(240) for x in range(320))
    assert has_non_bg
    assert forester_hut is not None and lumber_camp is not None
