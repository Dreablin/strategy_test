"""Forester panel should receive production/status text from worker manager."""

from game.buildings.forester_hut import ForesterHut
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.camera import Camera
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.input import GameInput
from game.ui.placement import PlacementController
from game.world import World
from game.workers import WorkerManager


def test_panel_production_status_exists_for_forester_hut() -> None:
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile()).level = 10
    hut = registry.place(ForesterHut, near_town_hall_tile(12, 4))
    placement = PlacementController(world, registry, Camera())
    workers = WorkerManager(registry)
    inp = GameInput(world, registry, placement, workers, Camera())
    inp._panel = hut  # noqa: SLF001 - direct panel setup for focused regression test
    status = inp._panel_production_status()  # noqa: SLF001
    assert status is not None
    assert status != "N/A"
