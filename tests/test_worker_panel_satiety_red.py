"""RED tests for worker panel satiety line (T261); `WorkerPanel.body_lines` + satiety in T262."""

from __future__ import annotations

from game.buildings.lumber_camp import LumberCamp
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.config import WORKER_TILE_TRAVEL_MS, near_town_hall_tile, town_hall_origin_tile
from game.ui.worker_panel import WorkerPanel
from game.worker_models import TransportTask, Worker
from game.worker_satiety import MAX_WORKER_SATIETY
from game.world import World


def _find_satiety_line(lines: list[str]) -> str:
    for ln in lines:
        if ln.strip().lower().startswith("satiety:"):
            return ln
    raise AssertionError(f"No Satiety line in {lines!r}")


def _find_move_speed_line(lines: list[str]) -> str:
    for ln in lines:
        if ln.strip().lower().startswith("move speed:"):
            return ln
    raise AssertionError(f"No Move speed line in {lines!r}")


def test_worker_panel_body_lines_include_satiety_idle_carrier() -> None:
    worker = Worker("CARRIER", stand_tile=near_town_hall_tile())
    worker.state = "idle"
    worker.idle = True
    worker.satiety = MAX_WORKER_SATIETY
    lines = WorkerPanel.body_lines(worker)
    sat = _find_satiety_line(lines)
    assert f"{MAX_WORKER_SATIETY}/{MAX_WORKER_SATIETY}" in sat.replace(" ", "")


def test_worker_panel_body_lines_include_satiety_carrier_carrying() -> None:
    world = World(world_seed=1)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    camp = registry.place(LumberCamp, near_town_hall_tile(12, 8))
    camp.construction_site = None

    worker = Worker("CARRIER", stand_tile=near_town_hall_tile())
    worker.carrying = "wood"
    worker.satiety = 4_321
    worker.state = "moving"
    worker.idle = False

    lines = WorkerPanel.body_lines(worker)
    sat = _find_satiety_line(lines)
    assert "4321" in sat
    assert str(MAX_WORKER_SATIETY) in sat
    assert "Carrying:" in "\n".join(lines)


def test_worker_panel_body_lines_include_satiety_with_active_transport_task() -> None:
    world = World(world_seed=2)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    th = registry.place(TownHall, town_hall_origin_tile())
    camp = registry.place(LumberCamp, near_town_hall_tile(14, 8))
    camp.construction_site = None

    worker = Worker("CARRIER", stand_tile=near_town_hall_tile())
    worker.transport_task = TransportTask(resource="boards", source=camp, target=th, purpose="generic")
    worker.satiety = 2_000
    worker.state = "moving"

    lines = WorkerPanel.body_lines(worker)
    sat = _find_satiety_line(lines)
    assert "2000" in sat
    assert str(MAX_WORKER_SATIETY) in sat
    assert any("Task:" in ln for ln in lines)
    assert any("Resource:" in ln for ln in lines)


def test_worker_panel_body_lines_show_dining_state_labels() -> None:
    worker = Worker("BUILDER", stand_tile=near_town_hall_tile())
    worker.state = "waiting_for_meal"

    lines = WorkerPanel.body_lines(worker)

    assert "State: Waiting for meal" in lines


def test_worker_panel_body_lines_include_effective_move_speed() -> None:
    worker = Worker("CARRIER", stand_tile=near_town_hall_tile())
    worker.characteristics.add_permanent(("test", "speed"), "move_speed_mult", 0.20)

    lines = WorkerPanel.body_lines(worker)
    speed = _find_move_speed_line(lines)
    expected_travel_ms = int(round(WORKER_TILE_TRAVEL_MS / 1.20))

    assert "1.20x" in speed
    assert f"{expected_travel_ms} ms/tile" in speed


def test_worker_panel_body_lines_include_zero_satiety_move_penalty() -> None:
    worker = Worker("CARRIER", stand_tile=near_town_hall_tile())
    worker.characteristics.add_permanent(("test", "speed"), "move_speed_mult", 0.20)
    worker.satiety = 0

    lines = WorkerPanel.body_lines(worker)
    speed = _find_move_speed_line(lines)
    expected_travel_ms = int(round(WORKER_TILE_TRAVEL_MS / 0.60))

    assert "0.60x" in speed
    assert f"{expected_travel_ms} ms/tile" in speed
