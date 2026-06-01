"""RED tests for worker panel satiety line (T261); `WorkerPanel.body_lines` + satiety in T262."""

from __future__ import annotations

from game import i18n
from game.buildings.lumber_camp import LumberCamp
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.config import WORKER_TILE_TRAVEL_MS, near_town_hall_tile, town_hall_origin_tile
from game.ui.worker_labels import worker_display_label
from game.ui.worker_panel import WorkerPanel
from game.worker_models import TransportTask, Worker
from game.worker_satiety import MAX_WORKER_SATIETY
from game.world import World


def test_worker_panel_body_lines_include_satiety_idle_carrier() -> None:
    worker = Worker("CARRIER", stand_tile=near_town_hall_tile())
    worker.state = "idle"
    worker.idle = True
    worker.satiety = MAX_WORKER_SATIETY
    lines = WorkerPanel.body_lines(worker)
    expected = i18n.t("ui.worker.satiety", current=MAX_WORKER_SATIETY, max=MAX_WORKER_SATIETY)
    assert expected in lines


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
    assert i18n.t("ui.worker.satiety", current=4321, max=MAX_WORKER_SATIETY) in lines
    assert i18n.t("ui.worker.carrying", resource=i18n.t("resource.wood")) in lines


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
    assert i18n.t("ui.worker.satiety", current=2000, max=MAX_WORKER_SATIETY) in lines
    assert i18n.t("ui.worker.task", task=i18n.t("status.worker.purpose.generic")) in lines
    assert i18n.t("ui.worker.resource", resource=i18n.t("resource.boards")) in lines


def test_worker_panel_body_lines_show_dining_state_labels() -> None:
    worker = Worker("BUILDER", stand_tile=near_town_hall_tile())
    worker.state = "waiting_for_meal"

    lines = WorkerPanel.body_lines(worker)

    assert i18n.t(
        "ui.worker.state",
        state=i18n.t("status.worker.waiting_for_meal"),
    ) in lines


def test_worker_panel_body_lines_include_effective_move_speed() -> None:
    worker = Worker("CARRIER", stand_tile=near_town_hall_tile())
    worker.characteristics.add_permanent(("test", "speed"), "move_speed_mult", 0.20)

    lines = WorkerPanel.body_lines(worker)
    expected_travel_ms = int(round(WORKER_TILE_TRAVEL_MS / 1.20))
    expected = i18n.t("ui.worker.move_speed", mult="1.20", travel_ms=expected_travel_ms)

    assert expected in lines


def test_worker_panel_body_lines_include_zero_satiety_move_penalty() -> None:
    worker = Worker("CARRIER", stand_tile=near_town_hall_tile())
    worker.characteristics.add_permanent(("test", "speed"), "move_speed_mult", 0.20)
    worker.satiety = 0

    lines = WorkerPanel.body_lines(worker)
    expected_travel_ms = int(round(WORKER_TILE_TRAVEL_MS / 0.60))
    expected = i18n.t("ui.worker.move_speed", mult="0.60", travel_ms=expected_travel_ms)

    assert expected in lines


def test_worker_panel_body_lines_ru_smoke(use_locale) -> None:
    with use_locale("ru"):
        worker = Worker("CARRIER", stand_tile=near_town_hall_tile())
        worker.state = "waiting_for_meal"
        lines = WorkerPanel.body_lines(worker)
        assert worker_display_label("CARRIER") == i18n.t("worker.CARRIER")
        assert i18n.t(
            "ui.worker.state",
            state=i18n.t("status.worker.waiting_for_meal"),
        ) in lines
