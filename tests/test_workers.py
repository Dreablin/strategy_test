"""Worker manager: hire, reassign, demolition (PRD F-WORK / F-DEMO)."""

import pytest

from game.buildings.base import Building
from game.buildings.farm import Farm
from game.buildings.field import WHEAT_PHASE_2, Field
from game.buildings.iron_mine import IronMine
from game.buildings.lumber_camp import LumberCamp
from game.buildings.mill import Mill
from game.buildings.registry import BuildingRegistry
from game.buildings.school import School
from game.buildings.sawmill import Sawmill
from game.buildings.stone_mine import StoneMine
from game.buildings.town_hall import TownHall
from game.characteristics import Characteristics
from game.config import building_worker_effects, near_town_hall_tile, town_hall_origin_tile
from game.construction import ConstructionSite
from game.iron import IronDeposit
from game.trees import Tree, TreeStage
from game.world import World
from game.workers import (
    CHOP_DURATION_MS,
    Worker,
    WorkerManager,
    TransportTask,
    building_center_tile,
    construction_transport_tasks,
    sawmill_input_transport_tasks,
    sawmill_output_transport_tasks,
    town_hall_spawn_tile,
)


class WheatConsumer(Building):
    type_tag = "WHEAT_CONSUMER"
    __slots__ = ("active", "wheat_in")

    def __init__(self, level: int = 1, grid_pos: tuple[int, int] | None = None) -> None:
        super().__init__(level, grid_pos)
        self.active = True
        self.wheat_in = 0

    def input_capacity(self) -> int:
        return 2

    def input_amount(self) -> int:
        return self.wheat_in

    def add_wheat_in(self, amount: int) -> None:
        self.wheat_in += int(amount)


def test_building_center_tile_for_2x2() -> None:
    b = LumberCamp(level=1, grid_pos=(10, 8))
    assert building_center_tile(b) == (11, 9)


def test_demolition_parks_assigned_worker_on_center_tile() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    camp = registry.place(LumberCamp, near_town_hall_tile(8, 8))
    center = building_center_tile(camp)
    wm = WorkerManager()
    w = Worker("LUMBERJACK")
    wm.add_worker(w)
    wm.assign_to_building(w, camp)
    assert not w.idle
    registry.demolish(camp, wm)
    assert w.idle
    assert w.assigned_building is None
    assert w.stand_tile == center


def test_demolition_does_not_affect_other_workers() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    a = registry.place(LumberCamp, near_town_hall_tile(4, 4))
    b = registry.place(LumberCamp, near_town_hall_tile(14, 8))
    wm = WorkerManager()
    w1 = Worker("LUMBERJACK")
    w2 = Worker("LUMBERJACK")
    wm.add_worker(w1)
    wm.add_worker(w2)
    wm.assign_to_building(w1, a)
    wm.assign_to_building(w2, b)
    registry.demolish(a, wm)
    assert w1.idle and w1.assigned_building is None
    assert not w2.idle and w2.assigned_building is b


def test_hire_is_free_and_returns_worker() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    wm = WorkerManager(registry)
    wheat_before = town_hall.warehouse_amount("wheat")
    w = wm.hire("LUMBERJACK")
    assert w is not None
    assert w.type_tag == "LUMBERJACK"
    assert w.current_tile == town_hall_spawn_tile(town_hall)
    assert town_hall.warehouse_amount("wheat") == wheat_before


def test_transport_queue_size_reports_pending_delivery_tasks() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    camp = registry.place(LumberCamp, near_town_hall_tile(8, 8))
    wm = WorkerManager(registry)

    assert wm.transport_queue_size() == 0
    wm.enqueue_transport_task(resource="wood", source=town_hall, target=camp, amount=2)

    assert wm.transport_queue_size() == 2


def test_active_transport_count_reports_assigned_delivery_tasks() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    camp = registry.place(LumberCamp, near_town_hall_tile(8, 8))
    wm = WorkerManager(registry)
    carrier = Worker("CARRIER")
    lumberjack = Worker("LUMBERJACK")
    carrier.transport_task = TransportTask("wood", town_hall, camp)
    wm.add_worker(carrier)
    wm.add_worker(lumberjack)

    assert wm.active_transport_count() == 1


def test_bootstrap_starting_workers_near_town_hall_spawns_two_carriers_and_builder() -> None:
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    wm = WorkerManager(registry)
    wm.bootstrap_starting_workers_near_town_hall(town_hall)
    workers = wm.workers()
    assert len(workers) == 3
    assert [w.type_tag for w in workers] == ["CARRIER", "CARRIER", "BUILDER"]
    assert town_hall.grid_pos is not None
    _, gy = town_hall.grid_pos
    south_y = gy + TownHall.footprint[1]
    for w in workers:
        assert world.is_in_grass(*w.current_tile)
        assert not world.is_occupied(*w.current_tile)
        assert w.current_tile[1] == south_y


def test_hire_without_explicit_source_uses_latest_school_when_present() -> None:
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    registry.place(School, near_town_hall_tile(8, 8))
    school_b = registry.place(School, near_town_hall_tile(18, 8))
    wm = WorkerManager(registry)

    hired = wm.hire("LUMBERJACK")
    assert hired is not None
    sx, sy = school_b.grid_pos
    sw, sh = school_b.footprint
    assert hired.current_tile == (sx + sw // 2, sy + sh)


def test_hire_sawyer_from_school_spawns_near_school() -> None:
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    school = registry.place(School, near_town_hall_tile(8, 8))
    school.construction_site = None
    wm = WorkerManager(registry)

    hired = wm.hire("SAWYER", source_building=school)
    assert hired is not None
    sx, sy = school.grid_pos
    sw, sh = school.footprint
    assert hired.current_tile == (sx + sw // 2, sy + sh)


def test_hire_baker_from_school_spawns_near_school_and_stays_unassigned() -> None:
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    school = registry.place(School, near_town_hall_tile(8, 8))
    school.construction_site = None
    wm = WorkerManager(registry)

    hired = wm.hire("BAKER", source_building=school)

    assert hired is not None
    assert hired.type_tag == "BAKER"
    sx, sy = school.grid_pos
    sw, sh = school.footprint
    assert hired.current_tile == (sx + sw // 2, sy + sh)
    assert hired.assigned_building is None
    assert hired.idle is True


def test_hire_animal_herder_from_school_spawns_near_school() -> None:
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    school = registry.place(School, near_town_hall_tile(8, 8))
    school.construction_site = None
    wm = WorkerManager(registry)

    hired = wm.hire("ANIMAL_HERDER", source_building=school)

    assert hired is not None
    assert hired.type_tag == "ANIMAL_HERDER"
    sx, sy = school.grid_pos
    sw, sh = school.footprint
    assert hired.current_tile == (sx + sw // 2, sy + sh)
    assert hired.assigned_building is None
    assert hired.idle is True


def test_reassign_all_assigns_sawyer_only_to_sawmill() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    camp = registry.place(LumberCamp, near_town_hall_tile(8, 8))
    sawmill = registry.place(Sawmill, near_town_hall_tile(14, 8))
    camp.construction_site = None
    sawmill.construction_site = None
    wm = WorkerManager(registry)
    sawyer = Worker("SAWYER")
    wm.add_worker(sawyer)

    wm.reassign_all()

    assert sawyer.assigned_building is sawmill
    assert sawyer.assigned_building is not camp


def test_sawyer_starts_processing_cycle_when_sawmill_ready() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    sawmill = registry.place(Sawmill, near_town_hall_tile(12, 10))
    sawmill.construction_site = None
    sawmill.add_wood_in(1)
    wm = WorkerManager(registry, now_ms_fn=lambda: 5_000)
    sawyer = Worker("SAWYER")
    wm.add_worker(sawyer)
    wm.assign_to_building(sawyer, sawmill)
    sawyer.state = "working"
    sawyer.idle = False
    sawyer.current_tile = (sawmill.grid_pos[0] + 1, sawmill.grid_pos[1] + 1)  # type: ignore[index]

    wm.update(5_000)

    assert sawyer.assigned_building is sawmill
    assert sawyer.state == "processing"
    assert sawmill.processing_started_ms == 5_000
    assert sawmill.progress_state(5_000) == "processing"


def test_sawyer_does_not_start_processing_when_output_full() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    sawmill = registry.place(Sawmill, near_town_hall_tile(14, 10))
    sawmill.construction_site = None
    sawmill.add_wood_in(1)
    sawmill.add_boards_out(sawmill.output_capacity())
    wm = WorkerManager(registry, now_ms_fn=lambda: 5_000)
    sawyer = Worker("SAWYER")
    wm.add_worker(sawyer)
    wm.assign_to_building(sawyer, sawmill)
    sawyer.state = "working"
    sawyer.idle = False

    wm.update(5_000)

    assert sawyer.assigned_building is sawmill
    assert sawyer.state != "processing"
    assert sawmill.processing_started_ms == 0


def test_sawyer_processing_completes_consumes_input_and_rests() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    sawmill = registry.place(Sawmill, near_town_hall_tile(15, 10))
    sawmill.construction_site = None
    sawmill.add_wood_in(1)
    wm = WorkerManager(registry, now_ms_fn=lambda: 0)
    sawyer = Worker("SAWYER")
    wm.add_worker(sawyer)
    wm.assign_to_building(sawyer, sawmill)
    sawyer.state = "working"
    sawyer.idle = False

    wm.update(1_000)
    assert sawyer.state == "processing"
    assert sawmill.processing_started_ms == 1_000

    done_ms = sawmill.processing_started_ms + sawmill.processing_duration_ms
    wm.update(done_ms)

    assert sawmill.input_amount() == 0
    assert sawmill.output_amount() == 1
    assert sawmill.processing_started_ms == 0
    assert sawyer.state == "resting"
    assert sawyer.camp_wait_until_ms > done_ms


def test_sawyer_cycle_duration_scales_by_level() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    sawmill = registry.place(Sawmill, near_town_hall_tile(16, 10))
    sawmill.construction_site = None
    sawmill.level = 5
    sawmill.add_wood_in(1)
    wm = WorkerManager(registry, now_ms_fn=lambda: 0)
    sawyer = Worker("SAWYER")
    wm.add_worker(sawyer)
    wm.assign_to_building(sawyer, sawmill)
    sawyer.state = "working"
    sawyer.idle = False

    wm.update(1_000)
    # Level 5 => 30_000 * (1 - 0.02 * 4) = 27_600ms.
    wm.update(28_000)
    assert sawyer.state == "processing"
    assert sawmill.output_amount() == 0

    wm.update(28_700)
    assert sawyer.state == "resting"
    assert sawmill.output_amount() == 1


def test_sawyer_does_not_start_processing_when_inactive_or_no_input() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    sawmill = registry.place(Sawmill, near_town_hall_tile(18, 10))
    sawmill.construction_site = None
    wm = WorkerManager(registry, now_ms_fn=lambda: 0)
    sawyer = Worker("SAWYER")
    wm.add_worker(sawyer)
    wm.assign_to_building(sawyer, sawmill)
    sawyer.state = "working"

    sawmill.set_active(False)
    sawmill.add_wood_in(1)
    wm.update(1_000)
    assert sawyer.state == "resting"
    assert sawyer.current_tile == building_center_tile(sawmill)
    assert sawmill.processing_started_ms == 0

    sawmill.set_active(True)
    sawyer.state = "working"
    sawmill.take_wood_in(1)
    wm.update(2_000)
    assert sawyer.state == "working"
    assert sawmill.processing_started_ms == 0


def test_sawyer_does_not_start_processing_when_under_construction_or_absent() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    sawmill = registry.place(Sawmill, near_town_hall_tile(20, 10))
    sawmill.construction_site = None
    sawmill.add_wood_in(1)
    wm = WorkerManager(registry, now_ms_fn=lambda: 0)

    # No assigned sawyer: update must not begin processing.
    wm.update(1_000)
    assert sawmill.processing_started_ms == 0

    sawyer = Worker("SAWYER")
    wm.add_worker(sawyer)
    wm.assign_to_building(sawyer, sawmill)
    sawyer.state = "working"
    sawmill.construction_site = ConstructionSite(
        required_resources={},
        delivered_resources={},
        build_time_ms=1_000,
        build_started_ms=None,
        builder=None,
        target_level=2,
    )
    wm.update(2_000)
    assert sawyer.state == "working"
    assert sawmill.processing_started_ms == 0


def test_sawyer_inactive_mid_cycle_finishes_current_then_blocks_next() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    sawmill = registry.place(Sawmill, near_town_hall_tile(22, 10))
    sawmill.construction_site = None
    sawmill.add_wood_in(2)
    wm = WorkerManager(registry, now_ms_fn=lambda: 0)
    sawyer = Worker("SAWYER")
    wm.add_worker(sawyer)
    wm.assign_to_building(sawyer, sawmill)
    sawyer.state = "working"

    wm.update(1_000)
    assert sawyer.state == "processing"
    sawmill.set_active(False)

    wm.update(31_000)
    assert sawmill.output_amount() == 1
    assert sawmill.input_amount() == 1
    assert sawyer.state == "resting"

    wm.update(41_001)
    assert sawyer.state == "resting"
    assert sawyer.current_tile == building_center_tile(sawmill)
    assert sawmill.processing_started_ms == 0
    wm.update(42_000)
    assert sawyer.state == "resting"
    assert sawmill.output_amount() == 1


def test_sawyer_stays_resting_inside_when_sawmill_inactive() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    sawmill = registry.place(Sawmill, near_town_hall_tile(23, 10))
    sawmill.construction_site = None
    wm = WorkerManager(registry, now_ms_fn=lambda: 0)
    sawyer = Worker("SAWYER")
    wm.add_worker(sawyer)
    wm.assign_to_building(sawyer, sawmill)
    sawmill.set_active(False)

    sawyer.state = "resting"
    sawyer.camp_wait_until_ms = 5_000
    sawyer.current_tile = (0, 0)
    wm.update(6_000)

    assert sawyer.state == "resting"
    assert sawyer.current_tile == building_center_tile(sawmill)


def test_sawyer_enters_sawmill_before_processing_starts() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    sawmill = registry.place(Sawmill, near_town_hall_tile(24, 10))
    sawmill.construction_site = None
    sawmill.add_wood_in(1)
    wm = WorkerManager(registry, now_ms_fn=lambda: 0)
    sawyer = Worker("SAWYER")
    wm.add_worker(sawyer)
    wm.assign_to_building(sawyer, sawmill)
    sawyer.state = "working"
    sawyer.current_tile = (0, 0)

    wm.update(1_000)
    assert sawyer.current_tile == building_center_tile(sawmill)
    assert sawyer.state == "working"
    assert sawmill.processing_started_ms == 0

    wm.update(2_000)
    assert sawyer.state == "processing"
    assert sawmill.processing_started_ms == 2_000


def test_hired_worker_has_characteristics_defaults() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    wm = WorkerManager(registry)

    worker = wm.hire("LUMBERJACK")

    assert worker is not None
    assert isinstance(worker.characteristics, Characteristics)
    assert worker.characteristics.move_speed_mult == 1.0
    assert worker.characteristics.gather_speed_mult == 1.0


def test_worker_applies_configured_global_and_type_effects(monkeypatch: pytest.MonkeyPatch) -> None:
    import game.config as config

    settings = {
        **config.SETTINGS,
        "workers": {
            **config.SETTINGS["workers"],
            "effects": {
                "global": {"move_speed_mult": 0.05},
                "by_type": {"CARRIER": {"move_speed_mult": 0.10, "gather_speed_mult": -0.05}},
            },
        },
    }
    monkeypatch.setattr(config, "SETTINGS", settings)

    worker = Worker("CARRIER")

    assert worker.characteristics.move_speed_mult == pytest.approx(1.15)
    assert worker.characteristics.gather_speed_mult == pytest.approx(0.95)


def test_worker_refresh_configured_effects_removes_deleted_config_stats(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import game.config as config

    settings = {
        **config.SETTINGS,
        "workers": {
            **config.SETTINGS["workers"],
            "effects": {
                "global": {"move_speed_mult": 0.05},
                "by_type": {"CARRIER": {"gather_speed_mult": 0.20}},
            },
        },
    }
    monkeypatch.setattr(config, "SETTINGS", settings)
    worker = Worker("CARRIER")
    assert worker.characteristics.move_speed_mult == pytest.approx(1.05)
    assert worker.characteristics.gather_speed_mult == pytest.approx(1.20)

    settings = {
        **config.SETTINGS,
        "workers": {
            **config.SETTINGS["workers"],
            "effects": {
                "global": {},
                "by_type": {"CARRIER": {"move_speed_mult": -0.10}},
            },
        },
    }
    monkeypatch.setattr(config, "SETTINGS", settings)
    worker.refresh_configured_effects()

    assert worker.characteristics.move_speed_mult == pytest.approx(0.90)
    assert worker.characteristics.gather_speed_mult == pytest.approx(1.0)


def test_worker_manager_refresh_configured_effects_preserves_building_effects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import game.config as config

    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    camp = registry.place(LumberCamp, (10, 10))
    camp.level = 3
    wm = WorkerManager(registry)
    worker = Worker("LUMBERJACK")
    wm.add_worker(worker)
    wm.assign_to_building(worker, camp)
    building_effects = building_worker_effects("LUMBER_CAMP", 3)

    settings = {
        **config.SETTINGS,
        "workers": {
            **config.SETTINGS["workers"],
            "effects": {
                "global": {"move_speed_mult": 0.05},
                "by_type": {"LUMBERJACK": {"gather_speed_mult": 0.15}},
            },
        },
    }
    monkeypatch.setattr(config, "SETTINGS", settings)

    wm.refresh_configured_worker_effects()

    assert worker.characteristics.move_speed_mult == pytest.approx(
        1.0 + building_effects["move_speed_mult"] + 0.05
    )
    assert worker.characteristics.gather_speed_mult == pytest.approx(
        1.0 + building_effects["gather_speed_mult"] + 0.15
    )


def test_assign_to_building_applies_level_bonus_source() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    camp = registry.place(LumberCamp, (10, 10))
    camp.level = 3
    wm = WorkerManager()
    worker = Worker("LUMBERJACK")
    wm.add_worker(worker)

    wm.assign_to_building(worker, camp)

    effects = building_worker_effects("LUMBER_CAMP", 3)
    assert worker.characteristics.move_speed_mult == 1.0 + effects["move_speed_mult"]
    assert worker.characteristics.gather_speed_mult == 1.0 + effects["gather_speed_mult"]


def test_notify_demolished_clears_building_level_bonus_source() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    camp = registry.place(LumberCamp, (12, 12))
    camp.level = 4
    wm = WorkerManager(registry=registry)
    worker = Worker("LUMBERJACK")
    wm.add_worker(worker)
    wm.assign_to_building(worker, camp)

    effects = building_worker_effects("LUMBER_CAMP", 4)
    assert worker.characteristics.move_speed_mult == 1.0 + effects["move_speed_mult"]
    wm.notify_demolished(camp)

    assert worker.characteristics.move_speed_mult == 1.0
    assert worker.characteristics.gather_speed_mult == 1.0


def test_reassign_to_different_building_swaps_bonus_source() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    camp_a = registry.place(LumberCamp, near_town_hall_tile(4, 4))
    camp_b = registry.place(LumberCamp, near_town_hall_tile(14, 8))
    camp_a.level = 2
    camp_b.level = 5
    wm = WorkerManager()
    worker = Worker("LUMBERJACK")
    wm.add_worker(worker)

    wm.assign_to_building(worker, camp_a)
    effects_a = building_worker_effects("LUMBER_CAMP", 2)
    assert worker.characteristics.move_speed_mult == 1.0 + effects_a["move_speed_mult"]

    wm.assign_to_building(worker, camp_b)
    effects_b = building_worker_effects("LUMBER_CAMP", 5)
    assert worker.characteristics.move_speed_mult == 1.0 + effects_b["move_speed_mult"]
    assert worker.characteristics.gather_speed_mult == 1.0 + effects_b["gather_speed_mult"]


def test_carrier_transport_task_does_not_apply_source_or_target_building_effects() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    source = registry.place(LumberCamp, near_town_hall_tile(4, 4))
    target = registry.place(LumberCamp, near_town_hall_tile(14, 8))
    source.level = 5
    target.level = 5
    wm = WorkerManager(registry)
    carrier = Worker("CARRIER")
    wm.add_worker(carrier)

    wm.enqueue_transport_task(resource="wood", source=source, target=target, amount=1)

    assert carrier.assigned_building is None
    assert carrier.characteristics.move_speed_mult == 1.0
    assert carrier.characteristics.gather_speed_mult == 1.0


def test_hire_does_not_consume_warehouse_wheat() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    wheat_before = town_hall.warehouse_amount("wheat")
    wm = WorkerManager(registry)
    assert wm.hire("LUMBERJACK") is not None
    assert town_hall.warehouse_amount("wheat") == wheat_before


def test_reassign_all_assigns_one_idle_lumberjack_to_empty_lumber_camp() -> None:
    world = World(world_seed=0)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    world._iron.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    camp = registry.place(LumberCamp, (10, 10))
    camp.construction_site = None
    wm = WorkerManager(registry)
    wm.add_worker(Worker("LUMBERJACK"))
    wm.reassign_all()
    assert wm.is_staffed(camp)
    w = wm.workers()[0]
    assert not w.idle
    assert w.assigned_building is camp


def test_update_completes_construction_and_reassigns_with_idle_builder() -> None:
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    camp = registry.place(LumberCamp, near_town_hall_tile(8, 8))
    camp.construction_site = ConstructionSite(
        required_resources={"wood": 2},
        delivered_resources={"wood": 2},
        build_time_ms=1_000,
        build_started_ms=100,
        builder=None,
        target_level=1,
    )
    builder = Worker("BUILDER")
    builder.idle = False
    builder.state = "building"
    builder.assigned_building = camp
    camp.construction_site.builder = builder

    wm = WorkerManager(registry, now_ms_fn=lambda: 1_100)
    wm.add_worker(builder)

    wm.update(1_100)

    assert camp.is_under_construction is False
    assert builder.idle is True
    assert builder.state == "idle"
    assert builder.assigned_building is None
    gx, gy = camp.grid_pos  # type: ignore[assignment]
    w, h = type(camp).footprint
    assert builder.current_tile == (gx + w // 2, gy + h)
    assert not world.is_occupied(*builder.current_tile)


def test_builder_completion_fallback_uses_building_center_when_no_approach() -> None:
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    camp = registry.place(LumberCamp, near_town_hall_tile(8, 8))
    camp.construction_site = ConstructionSite(
        required_resources={"wood": 2},
        delivered_resources={"wood": 2},
        build_time_ms=1_000,
        build_started_ms=100,
        builder=None,
        target_level=1,
    )
    cx, cy = camp.grid_pos  # type: ignore[assignment]
    for y in range(cy - 1, cy + 3):
        for x in range(cx - 1, cx + 3):
            if cx <= x <= cx + 1 and cy <= y <= cy + 1:
                continue
            world.mark_occupied(x, y, 1, 1)
    builder = Worker("BUILDER")
    builder.idle = False
    builder.state = "building"
    builder.assigned_building = camp
    camp.construction_site.builder = builder
    wm = WorkerManager(registry, now_ms_fn=lambda: 1_100)
    wm.add_worker(builder)

    wm.update(1_100)

    assert builder.idle is True
    assert builder.state == "idle"
    assert builder.assigned_building is None
    assert builder.current_tile == building_center_tile(camp)


def test_idle_builder_targets_fully_supplied_site_and_starts_building() -> None:
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    camp = registry.place(LumberCamp, near_town_hall_tile(10, 10))
    camp.construction_site = ConstructionSite(
        required_resources={"wood": 2},
        delivered_resources={"wood": 2},
        build_time_ms=10_000,
        build_started_ms=None,
        builder=None,
        target_level=1,
    )
    bx, by = camp.grid_pos  # type: ignore[assignment]
    builder = Worker("BUILDER", stand_tile=(bx - 4, by))
    wm = WorkerManager(registry, now_ms_fn=lambda: 1_000)
    wm.add_worker(builder)

    wm.update(1_000)
    assert builder.state == "moving"
    assert builder.assigned_building is camp
    assert camp.construction_site is not None
    assert camp.construction_site.builder is builder
    assert camp.construction_site.build_started_ms is None

    wm.update(120_000)
    assert camp.construction_site is not None
    assert camp.construction_site.builder is builder
    assert camp.construction_site.build_started_ms == 120_000
    assert builder.state == "building"
    assert builder.current_tile == building_center_tile(camp)


def test_second_builder_does_not_target_site_reserved_by_moving_builder() -> None:
    world = World(world_seed=2)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    camp = registry.place(LumberCamp, near_town_hall_tile(10, 10))
    camp.construction_site = ConstructionSite(
        required_resources={"wood": 2},
        delivered_resources={"wood": 2},
        build_time_ms=10_000,
        build_started_ms=None,
        builder=None,
        target_level=1,
    )
    bx, by = camp.grid_pos  # type: ignore[assignment]
    first = Worker("BUILDER", stand_tile=(bx - 4, by))
    second = Worker("BUILDER", stand_tile=(bx - 3, by))
    wm = WorkerManager(registry, now_ms_fn=lambda: 1_000)
    wm.add_worker(first)
    wm.add_worker(second)

    wm.update(1_000)

    assert first.assigned_building is camp
    assert first.state == "moving"
    assert second.assigned_building is None
    assert second.state == "idle"
    assert camp.construction_site is not None
    assert camp.construction_site.builder is first
    assert camp.construction_site.build_started_ms is None


def test_reassign_all_does_not_assign_stonecutter_to_lumber_camp() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    registry.place(LumberCamp, (10, 10))
    wm = WorkerManager(registry)
    w = Worker("STONECUTTER")
    wm.add_worker(w)
    wm.reassign_all()
    assert w.idle
    assert w.assigned_building is None


def test_demolish_then_reassign_moves_worker_to_new_matching_building() -> None:
    world = World(world_seed=2)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    camp1 = registry.place(LumberCamp, (8, 8))
    camp2 = registry.place(LumberCamp, near_town_hall_tile())
    camp1.construction_site = None
    camp2.construction_site = None
    wm = WorkerManager(registry)
    w = Worker("LUMBERJACK")
    wm.add_worker(w)
    wm.assign_to_building(w, camp1)
    registry.demolish(camp1, wm)
    assert w.idle
    assert w.stand_tile == building_center_tile(camp1)
    wm.reassign_all()
    assert w.assigned_building is camp2
    assert not w.idle


def test_reassign_all_assigns_farmer_to_empty_farm() -> None:
    world = World(world_seed=0)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    town_hall.level = 5
    registry.place(LumberCamp, (4, 4))
    farm = registry.place(Farm, near_town_hall_tile(12, 4))
    mine_pos = (10, 20)
    world._iron[mine_pos] = IronDeposit(blocking=False)  # noqa: SLF001
    mine = registry.place(IronMine, mine_pos)
    farm.construction_site = None
    mine.construction_site = None
    wm = WorkerManager(registry)
    wm.add_worker(Worker("FARMER"))
    wm.reassign_all()
    assert wm.is_staffed(farm)
    assert not wm.is_staffed(mine)


def test_reassign_all_assigns_miner_to_empty_iron_mine() -> None:
    world = World(world_seed=0)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    world._iron.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    town_hall.level = 5
    registry.place(Farm, (4, 4))
    mine_pos = near_town_hall_tile(12, 4)
    world._iron[mine_pos] = IronDeposit(blocking=False)  # noqa: SLF001
    mine = registry.place(IronMine, mine_pos)
    mine.construction_site = None
    wm = WorkerManager(registry)
    wm.add_worker(Worker("MINER"))
    wm.reassign_all()
    assert wm.is_staffed(mine)


def test_reassign_all_sets_moving_path_to_reachable_approach_tile() -> None:
    world = World(world_seed=0)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    camp = registry.place(LumberCamp, near_town_hall_tile(8, 8))
    camp.construction_site = None
    wm = WorkerManager(registry)
    cx, cy = camp.grid_pos  # type: ignore[assignment]
    stand = (cx - 4, cy)
    w = Worker("LUMBERJACK", stand_tile=stand)
    wm.add_worker(w)

    wm.reassign_all()

    assert w.assigned_building is camp
    assert w.state == "moving"
    assert len(w.path) >= 2
    assert w.path[0] == stand
    end = w.path[-1]
    assert not world.is_occupied(*end)
    # Tree is only picked after the lumberjack reaches the camp.
    assert w.target_tree is None


def test_reassign_all_uses_current_time_for_move_start_no_first_frame_teleport() -> None:
    world = World(world_seed=0)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    world._iron.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    town_hall.level = 5
    mine_pos = (26, 26)
    world._iron[mine_pos] = IronDeposit(blocking=False)  # noqa: SLF001
    mine = registry.place(IronMine, mine_pos)
    mine.construction_site = None
    now_holder = {"t": 100_000}
    wm = WorkerManager(registry, now_ms_fn=lambda: now_holder["t"])
    w = Worker("MINER", stand_tile=(17, 19))
    wm.add_worker(w)

    wm.reassign_all()
    start = w.current_tile
    assert w.state == "moving"

    # 1 ms after assignment should still be on the same tile.
    now_holder["t"] = 100_001
    wm.update(now_holder["t"])
    assert w.current_tile == start


def test_reassign_all_keeps_worker_idle_when_no_approach_tile_reachable() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    camp = registry.place(LumberCamp, near_town_hall_tile(8, 8))
    gx, gy = camp.grid_pos  # type: ignore[assignment]
    for y in range(gy - 1, gy + 3):
        for x in range(gx - 1, gx + 3):
            if gx <= x <= gx + 1 and gy <= y <= gy + 1:
                continue
            world.mark_occupied(x, y, 1, 1)
    wm = WorkerManager(registry)
    w = Worker("LUMBERJACK", stand_tile=(gx - 5, gy))
    wm.add_worker(w)

    wm.reassign_all()

    assert w.idle
    assert w.assigned_building is None
    assert w.state == "idle"


def test_working_buildings_excludes_moving_worker_until_arrival() -> None:
    world = World(world_seed=0)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    camp = registry.place(LumberCamp, near_town_hall_tile(8, 8))
    camp.construction_site = None
    cx, cy = camp.grid_pos  # type: ignore[assignment]
    wm = WorkerManager(registry)
    w = Worker("LUMBERJACK", stand_tile=(cx - 4, cy))
    wm.add_worker(w)
    wm.reassign_all()

    assert camp not in wm.working_buildings()
    wm.update(120_000)
    assert camp in wm.working_buildings()


def test_worker_status_for_building_reports_on_the_way_then_assigned() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    camp = registry.place(LumberCamp, near_town_hall_tile(8, 8))
    camp.construction_site = None
    cx, cy = camp.grid_pos  # type: ignore[assignment]
    wm = WorkerManager(registry)
    w = Worker("LUMBERJACK", stand_tile=(cx - 4, cy))
    wm.add_worker(w)
    wm.reassign_all()

    assert wm.worker_status_for_building(camp) == "on the way"
    wm.update(120_000)
    assert wm.worker_status_for_building(camp) == "assigned"


def test_worker_status_for_building_reports_on_the_way_for_stonecutter_resource_walk() -> None:
    from game.buildings.stone_mine import StoneMine

    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    th = registry.place(TownHall, town_hall_origin_tile())
    th.level = 3
    mine = registry.place(StoneMine, near_town_hall_tile(5, 5))
    mine.construction_site = None
    mx, my = mine.grid_pos  # type: ignore[assignment]
    wm = WorkerManager(registry)
    w = Worker("STONECUTTER", stand_tile=(mx - 2, my))
    wm.add_worker(w)
    wm.assign_to_building(w, mine)
    w.start_move([(mx - 2, my), (mx - 1, my)], started_ms=0, move_state="going_to_stone")

    assert wm.worker_status_for_building(mine) == "on the way"


def test_production_status_for_building_no_worker_and_storage_full() -> None:
    camp = LumberCamp(level=1, grid_pos=(10, 10))
    wm = WorkerManager()

    assert wm.production_status_for_building(camp) == "No worker"

    w = Worker("LUMBERJACK")
    wm.add_worker(w)
    wm.assign_to_building(w, camp)
    camp.add_to_storage(camp.storage_capacity())
    assert wm.production_status_for_building(camp) == "Storage full"


def test_production_status_for_building_resting_and_gathering_states() -> None:
    camp = LumberCamp(level=1, grid_pos=(10, 10))
    now = {"t": 1000}
    wm = WorkerManager(registry=None, now_ms_fn=lambda: now["t"])
    w = Worker("LUMBERJACK")
    wm.add_worker(w)
    wm.assign_to_building(w, camp)

    w.state = "working"
    w.camp_wait_until_ms = 3000
    assert wm.production_status_for_building(camp) == "Resting"

    w.state = "chopping"
    assert wm.production_status_for_building(camp) == "Gathering"

    w.state = "returning"
    assert wm.production_status_for_building(camp) == "On the way"


def test_farm_production_status_reports_worker_action_states_and_hints() -> None:
    world = World(world_seed=0)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    farm = registry.place(Farm, near_town_hall_tile(10, 8))
    farm.construction_site = None
    field = registry.place(Field, near_town_hall_tile(7, 8))
    field.construction_site = None
    wm = WorkerManager(registry, now_ms_fn=lambda: 0)
    farmer = Worker("FARMER")
    wm.add_worker(farmer)
    wm.assign_to_building(farmer, farm)

    farmer.state = "moving"
    assert wm.production_status_for_building(farm) == "Moving"
    farmer.state = "sowing"
    assert wm.production_status_for_building(farm) == "Sowing"
    farmer.state = "harvesting"
    assert wm.production_status_for_building(farm) == "Harvesting"

    farm.stored = farm.storage_capacity()
    assert wm.production_status_for_building(farm) == "Storage full"

    farm.stored = 0
    wm._write_field_phase(field, WHEAT_PHASE_2)  # noqa: SLF001
    farmer.state = "working_field"
    assert wm.production_status_for_building(farm) == "No fields in radius"
    wm._write_field_phase(field, "EMPTY")  # noqa: SLF001
    assert wm.production_status_for_building(farm) == "Resting"


def test_farm_worker_status_reports_farm_specific_states() -> None:
    world = World(world_seed=0)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    farm = registry.place(Farm, near_town_hall_tile(10, 8))
    farm.construction_site = None
    wm = WorkerManager(registry)
    farmer = Worker("FARMER")
    wm.add_worker(farmer)
    wm.assign_to_building(farmer, farm)

    farmer.state = "going_to_field"
    assert wm.worker_status_for_building(farm) == "moving"
    farmer.state = "sowing"
    assert wm.worker_status_for_building(farm) == "sowing"
    farmer.state = "harvesting"
    assert wm.worker_status_for_building(farm) == "harvesting"
    farmer.state = "working_field"
    assert wm.worker_status_for_building(farm) == "resting"


def test_production_status_for_sawmill_blocked_reason_states() -> None:
    sawmill = Sawmill(level=1, grid_pos=(10, 10))
    wm = WorkerManager()
    assert wm.production_status_for_building(sawmill) == "No worker"

    worker = Worker("SAWYER")
    wm.add_worker(worker)
    wm.assign_to_building(worker, sawmill)
    sawmill.set_active(False)
    assert wm.production_status_for_building(sawmill) == "Inactive"

    sawmill.set_active(True)
    assert wm.production_status_for_building(sawmill) == "No wood"
    sawmill.add_wood_in(1)
    sawmill.add_boards_out(sawmill.output_capacity())
    assert wm.production_status_for_building(sawmill) == "Output full"

    sawmill.take_boards_out(sawmill.output_capacity())
    worker.state = "resting"
    assert wm.production_status_for_building(sawmill) == "Resting"


def test_worker_status_for_under_construction_reports_resting_or_empty() -> None:
    camp = LumberCamp(level=1, grid_pos=(10, 10))
    camp.construction_site = ConstructionSite(
        required_resources={"wood": 2},
        delivered_resources={},
        build_time_ms=10_000,
        build_started_ms=None,
        builder=None,
        target_level=2,
    )
    wm = WorkerManager()
    assert wm.worker_status_for_building(camp) == "empty"

    worker = Worker("LUMBERJACK")
    wm.add_worker(worker)
    wm.assign_to_building(worker, camp)
    worker.state = "resting"
    assert wm.worker_status_for_building(camp) == "resting"


def test_production_status_for_under_construction_is_explicit() -> None:
    camp = LumberCamp(level=1, grid_pos=(10, 10))
    camp.construction_site = ConstructionSite(
        required_resources={"wood": 2},
        delivered_resources={},
        build_time_ms=10_000,
        build_started_ms=None,
        builder=None,
        target_level=2,
    )
    wm = WorkerManager()
    assert wm.production_status_for_building(camp) == "Under construction"

    worker = Worker("LUMBERJACK")
    wm.add_worker(worker)
    wm.assign_to_building(worker, camp)
    worker.state = "resting"
    assert wm.production_status_for_building(camp) == "Under construction"


def test_demolish_moving_worker_becomes_idle_at_current_tile() -> None:
    world = World(world_seed=0)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    camp = registry.place(LumberCamp, near_town_hall_tile(8, 8))
    camp.construction_site = None
    cx, cy = camp.grid_pos  # type: ignore[assignment]
    wm = WorkerManager(registry)
    w = Worker("LUMBERJACK", stand_tile=(cx - 4, cy))
    wm.add_worker(w)
    wm.reassign_all()
    assert w.assigned_building is camp
    assert w.state == "moving"

    wm.update(1_500)
    before = w.current_tile
    registry.demolish(camp, wm)

    assert w.idle
    assert w.state == "idle"
    assert w.current_tile == before
    assert w.assigned_building is None


def test_demolish_builder_walking_to_site_becomes_idle_at_current_tile() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    camp = registry.place(LumberCamp, near_town_hall_tile(10, 10))
    camp.construction_site = ConstructionSite(
        required_resources={"wood": 2},
        delivered_resources={"wood": 2},
        build_time_ms=10_000,
        build_started_ms=None,
        builder=None,
        target_level=1,
    )
    cx, cy = camp.grid_pos  # type: ignore[assignment]
    wm = WorkerManager(registry)
    builder = Worker("BUILDER", stand_tile=(cx - 4, cy))
    wm.add_worker(builder)
    wm.update(1_000)
    assert builder.assigned_building is camp
    assert builder.state == "moving"

    wm.update(1_500)
    before = builder.current_tile
    registry.demolish(camp, wm)

    assert builder.idle
    assert builder.state == "idle"
    assert builder.current_tile == before
    assert builder.assigned_building is None


def test_notify_demolished_builder_inside_site_becomes_idle_and_clears_site_builder() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    camp = registry.place(LumberCamp, near_town_hall_tile(8, 8))
    builder = Worker("BUILDER")
    builder.assigned_building = camp
    builder.idle = False
    builder.state = "building"
    builder.current_tile = building_center_tile(camp)
    camp.construction_site = ConstructionSite(
        required_resources={"wood": 2},
        delivered_resources={"wood": 2},
        build_time_ms=10_000,
        build_started_ms=1_000,
        builder=builder,
        target_level=1,
    )
    wm = WorkerManager(registry)
    wm.add_worker(builder)

    wm.notify_demolished(camp)

    assert builder.idle
    assert builder.state == "idle"
    assert builder.assigned_building is None
    assert builder.current_tile == building_center_tile(camp)
    assert camp.construction_site is not None
    assert camp.construction_site.builder is None

def test_reassign_all_does_not_retarget_worker_already_moving() -> None:
    world = World(world_seed=0)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    camp_a = registry.place(LumberCamp, near_town_hall_tile())
    camp_b = registry.place(LumberCamp, near_town_hall_tile(15, 15))
    camp_a.construction_site = None
    camp_b.construction_site = None
    ax, ay = camp_a.grid_pos  # type: ignore[assignment]
    wm = WorkerManager(registry)
    w = Worker("LUMBERJACK", stand_tile=(ax - 4, ay))
    wm.add_worker(w)
    wm.reassign_all()
    first_target = w.assigned_building
    assert first_target in {camp_a, camp_b}
    assert w.state == "moving"

    wm.reassign_all()
    assert w.assigned_building is first_target
    assert w.state == "moving"


def test_reassign_all_one_slot_two_workers_only_one_assigned() -> None:
    world = World(world_seed=0)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    camp = registry.place(LumberCamp, near_town_hall_tile(8, 8))
    camp.construction_site = None
    cx, cy = camp.grid_pos  # type: ignore[assignment]
    wm = WorkerManager(registry)
    w1 = Worker("LUMBERJACK", stand_tile=(cx - 4, cy))
    w2 = Worker("LUMBERJACK", stand_tile=(cx - 3, cy))
    wm.add_worker(w1)
    wm.add_worker(w2)

    wm.reassign_all()
    assigned = [w for w in (w1, w2) if w.assigned_building is camp]
    idle = [w for w in (w1, w2) if w.assigned_building is None and w.idle]
    assert len(assigned) == 1
    assert len(idle) == 1


def test_hire_unknown_worker_type_returns_none_and_keeps_resources() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    wm = WorkerManager(registry)
    wheat_before = town_hall.warehouse_amount("wheat")
    assert wm.hire("WIZARD") is None
    assert town_hall.warehouse_amount("wheat") == wheat_before


def test_hire_carrier_succeeds_and_worker_stays_unassigned() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    wm = WorkerManager(registry)

    carrier = wm.hire("CARRIER")
    assert carrier is not None
    assert carrier.type_tag == "CARRIER"
    wm.reassign_all()
    assert carrier.assigned_building is None


def test_hire_builder_succeeds_and_worker_stays_unassigned() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    wm = WorkerManager(registry)

    builder = wm.hire("BUILDER")
    assert builder is not None
    assert builder.type_tag == "BUILDER"
    wm.reassign_all()
    assert builder.assigned_building is None


def test_carrier_transports_from_lumber_camp_to_town_hall_warehouse() -> None:
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    camp = registry.place(LumberCamp, near_town_hall_tile(8, 8))
    wm = WorkerManager(registry, now_ms_fn=lambda: 0)

    carrier = wm.hire("CARRIER")
    assert carrier is not None
    camp.add_to_storage(1)
    wm.enqueue_transport_task(resource="wood", source=camp, target=town_hall, amount=1)

    for now_ms in range(0, 120_000, 500):
        wm.update(now_ms)
        if camp.stored == 0 and town_hall.warehouse_amount("wood") == 1:
            break

    assert camp.stored == 0
    assert town_hall.warehouse_amount("wood") == 1


def test_carrier_waits_2s_inside_buildings_on_pickup_and_dropoff() -> None:
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    camp = registry.place(LumberCamp, near_town_hall_tile(8, 8))
    wm = WorkerManager(registry, now_ms_fn=lambda: 0)
    carrier = wm.hire("CARRIER")
    assert carrier is not None
    camp.add_to_storage(1)
    wm.enqueue_transport_task(resource="wood", source=camp, target=town_hall, amount=1)

    pickup_started_ms: int | None = None
    for now_ms in range(0, 120_000, 250):
        wm.update(now_ms)
        if carrier.state == "carrier_loading":
            pickup_started_ms = now_ms
            break
    assert pickup_started_ms is not None
    assert camp.stored == 1

    wm.update(pickup_started_ms + 1_500)
    assert camp.stored == 1
    wm.update(pickup_started_ms + 2_100)
    assert camp.stored == 0

    unload_started_ms: int | None = None
    for now_ms in range(pickup_started_ms + 2_100, pickup_started_ms + 120_000, 250):
        wm.update(now_ms)
        if carrier.state == "carrier_unloading":
            unload_started_ms = now_ms
            break
    assert unload_started_ms is not None
    assert town_hall.warehouse_amount("wood") == 0

    wm.update(unload_started_ms + 1_500)
    assert town_hall.warehouse_amount("wood") == 0
    wm.update(unload_started_ms + 2_100)
    assert town_hall.warehouse_amount("wood") == 1
    tx, ty = town_hall.grid_pos  # type: ignore[misc]
    tw, th = type(town_hall).footprint
    assert carrier.current_tile == (tx + tw // 2, ty + th)


def test_construction_transport_tasks_generate_high_priority_from_town_hall_warehouse() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    camp = registry.place(LumberCamp, near_town_hall_tile(8, 8))
    camp.construction_site = ConstructionSite(
        required_resources={"wood": 3, "stone": 2},
        delivered_resources={"wood": 1},
        build_time_ms=10_000,
        build_started_ms=None,
        builder=None,
        target_level=1,
    )
    town_hall.add_to_warehouse("wood", 2)
    town_hall.add_to_warehouse("stone", 1)

    tasks = construction_transport_tasks(registry)

    assert len(tasks) == 3
    assert all(t.source is town_hall for t in tasks)
    assert all(t.target is camp for t in tasks)
    assert all(t.priority == 10 for t in tasks)
    assert sum(1 for t in tasks if t.resource == "wood") == 2
    assert sum(1 for t in tasks if t.resource == "stone") == 1


def test_construction_transport_tasks_ignore_non_construction_buildings() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    camp = registry.place(LumberCamp, near_town_hall_tile(8, 8))
    mine = registry.place(StoneMine, near_town_hall_tile(12, 8))
    camp.construction_site = None
    mine.construction_site = ConstructionSite(
        required_resources={"stone": 1},
        delivered_resources={},
        build_time_ms=10_000,
        build_started_ms=None,
        builder=None,
        target_level=1,
    )
    town_hall.add_to_warehouse("stone", 1)

    tasks = construction_transport_tasks(registry)

    assert len(tasks) == 1
    assert tasks[0].target is mine


def test_next_transport_task_drops_stale_construction_task_when_need_is_zero() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    camp = registry.place(LumberCamp, near_town_hall_tile(8, 8))
    camp.construction_site = ConstructionSite(
        required_resources={"wood": 1},
        delivered_resources={"wood": 1},
        build_time_ms=10_000,
        build_started_ms=None,
        builder=None,
        target_level=1,
    )
    town_hall.add_to_warehouse("wood", 1)
    wm = WorkerManager(registry)
    wm.enqueue_transport_task(resource="wood", source=town_hall, target=camp, amount=1, priority=10)

    picked = wm._next_transport_task()

    assert picked is None
    assert wm._transport_queue == []  # noqa: SLF001


def test_sawmill_input_transport_tasks_generate_low_priority_wood_refill() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    sawmill = registry.place(Sawmill, near_town_hall_tile(12, 8))
    sawmill.construction_site = None
    sawmill.set_active(True)
    sawmill.add_wood_in(1)
    town_hall.add_to_warehouse("wood", 2)

    tasks = sawmill_input_transport_tasks(registry)

    assert len(tasks) == 2
    assert all(t.resource == "wood" for t in tasks)
    assert all(t.source is town_hall for t in tasks)
    assert all(t.target is sawmill for t in tasks)
    assert all(t.priority == 0 for t in tasks)


def test_sawmill_input_transport_tasks_are_lower_priority_than_construction_tasks() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    camp = registry.place(LumberCamp, near_town_hall_tile(8, 8))
    sawmill = registry.place(Sawmill, near_town_hall_tile(12, 8))
    camp.construction_site = ConstructionSite(
        required_resources={"wood": 1},
        delivered_resources={},
        build_time_ms=10_000,
        build_started_ms=None,
        builder=None,
        target_level=1,
    )
    sawmill.construction_site = None
    sawmill.set_active(True)
    town_hall.add_to_warehouse("wood", 2)

    construction = construction_transport_tasks(registry)
    refill = sawmill_input_transport_tasks(registry)

    assert construction
    assert refill
    assert min(t.priority for t in construction) > max(t.priority for t in refill)


def test_update_enqueues_sawmill_refill_tasks_for_active_sawmill() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    camp = registry.place(LumberCamp, near_town_hall_tile(8, 8))
    sawmill = registry.place(Sawmill, near_town_hall_tile(14, 8))
    camp.construction_site = ConstructionSite(
        required_resources={"wood": 1},
        delivered_resources={},
        build_time_ms=10_000,
        build_started_ms=None,
        builder=None,
        target_level=1,
    )
    sawmill.construction_site = None
    town_hall.add_to_warehouse("wood", 2)
    wm = WorkerManager(registry)

    wm.update(1_000)
    first = wm._next_transport_task()
    second = wm._next_transport_task()
    assert first is not None
    assert second is not None
    assert first.target is camp
    assert first.priority == 10
    assert second.target is sawmill
    assert second.resource == "wood"
    assert second.priority == 0


def test_sawmill_output_transport_tasks_generate_boards_exports() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    sawmill = registry.place(Sawmill, near_town_hall_tile(16, 8))
    sawmill.construction_site = None
    sawmill.add_boards_out(2)

    tasks = sawmill_output_transport_tasks(registry)

    assert len(tasks) == 2
    assert all(t.resource == "boards" for t in tasks)
    assert all(t.source is sawmill for t in tasks)
    assert all(t.target is town_hall for t in tasks)
    assert all(t.priority == 0 for t in tasks)


def test_update_sawmill_output_enqueue_is_deduped_across_ticks() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    sawmill = registry.place(Sawmill, near_town_hall_tile(18, 8))
    sawmill.construction_site = None
    sawmill.add_boards_out(2)
    wm = WorkerManager(registry)

    wm.update(1_000)
    wm.update(2_000)
    wm.update(3_000)

    queued = [t for t in wm._transport_queue if t.resource == "boards"]  # noqa: SLF001
    assert len(queued) == 2
    assert all(t.source is sawmill for t in queued)


def test_farm_wheat_output_prefers_mill_space_after_inbound_reservations() -> None:
    world = World(world_seed=0)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    farm = registry.place(Farm, near_town_hall_tile(8, 8))
    mill = registry.place(Mill, near_town_hall_tile(16, 8))
    farm.construction_site = None
    mill.construction_site = None
    farm.stored = 3

    wm = WorkerManager(registry)
    wm.enqueue_transport_task(resource="wheat", source=town_hall, target=mill, amount=1)
    carrier = Worker("CARRIER")
    carrier.transport_task = TransportTask(resource="wheat", source=town_hall, target=mill)
    wm.add_worker(carrier)

    wm.update(1_000)

    wheat_from_farm = [t for t in wm._transport_queue if t.source is farm and t.resource == "wheat"]  # noqa: SLF001
    assert sum(1 for t in wheat_from_farm if t.target is mill) == 1
    assert sum(1 for t in wheat_from_farm if t.target is town_hall) == 2
    assert mill.input_amount() == 0


def test_farm_wheat_output_can_target_non_mill_wheat_consumer() -> None:
    world = World(world_seed=0)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    farm = registry.place(Farm, near_town_hall_tile(8, 8))
    consumer = registry.place(WheatConsumer, near_town_hall_tile(16, 8))
    farm.construction_site = None
    farm.stored = 1

    wm = WorkerManager(registry)
    wm.update(1_000)

    wheat_from_farm = [t for t in wm._transport_queue if t.source is farm and t.resource == "wheat"]  # noqa: SLF001
    assert len(wheat_from_farm) == 1
    assert wheat_from_farm[0].target is consumer


def test_lumberjack_output_prefers_sawmill_before_town_hall() -> None:
    world = World(world_seed=0)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    camp = registry.place(LumberCamp, near_town_hall_tile(8, 8))
    sawmill = registry.place(Sawmill, near_town_hall_tile(16, 8))
    camp.construction_site = None
    sawmill.construction_site = None
    wm = WorkerManager(registry)
    lumberjack = Worker("LUMBERJACK")
    wm.add_worker(lumberjack)
    wm.assign_to_building(lumberjack, camp)
    lumberjack.state = "depositing"
    lumberjack.carrying = "wood"

    wm.update(1_000)

    wood_tasks = [t for t in wm._transport_queue if t.source is camp and t.resource == "wood"]  # noqa: SLF001
    assert len(wood_tasks) == 1
    assert wood_tasks[0].target is sawmill
    assert camp.stored == 1


def test_carrier_refills_sawmill_wood_input_from_town_hall() -> None:
    world = World(world_seed=2)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    sawmill = registry.place(Sawmill, near_town_hall_tile(16, 8))
    sawmill.construction_site = None
    town_hall.add_to_warehouse("wood", 1)
    wm = WorkerManager(registry, now_ms_fn=lambda: 0)
    carrier = wm.hire("CARRIER")
    assert carrier is not None
    wm.enqueue_transport_task(resource="wood", source=town_hall, target=sawmill, amount=1)

    for now_ms in range(0, 120_000, 500):
        wm.update(now_ms)
        if sawmill.input_amount() >= 1:
            break

    assert sawmill.input_amount() == 1
    assert town_hall.warehouse_amount("wood") == 0


def test_carrier_exports_boards_from_sawmill_to_town_hall() -> None:
    world = World(world_seed=2)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    sawmill = registry.place(Sawmill, near_town_hall_tile(18, 8))
    sawmill.construction_site = None
    sawmill.add_boards_out(1)
    wm = WorkerManager(registry, now_ms_fn=lambda: 0)
    carrier = wm.hire("CARRIER")
    assert carrier is not None
    wm.enqueue_transport_task(resource="boards", source=sawmill, target=town_hall, amount=1)

    for now_ms in range(0, 300_000, 500):
        wm.update(now_ms)
        if town_hall.warehouse_amount("boards") >= 1:
            break

    assert town_hall.warehouse_amount("boards") == 1
    assert sawmill.output_amount() == 0


def test_carrier_redirects_wood_to_town_hall_if_sawmill_input_becomes_full_mid_route() -> None:
    world = World(world_seed=2)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    sawmill = registry.place(Sawmill, near_town_hall_tile(20, 8))
    sawmill.construction_site = None
    town_hall.add_to_warehouse("wood", 1)
    wm = WorkerManager(registry, now_ms_fn=lambda: 0)
    carrier = wm.hire("CARRIER")
    assert carrier is not None
    wm.enqueue_transport_task(resource="wood", source=town_hall, target=sawmill, amount=1)

    loading_ms = None
    for now_ms in range(0, 120_000, 500):
        wm.update(now_ms)
        if carrier.state == "carrier_loading":
            loading_ms = now_ms
            break
    assert loading_ms is not None
    wm.update(loading_ms + 2_100)
    assert carrier.carrying == "wood"

    sawmill.add_wood_in(sawmill.input_capacity())

    for now_ms in range(loading_ms + 2_200, loading_ms + 120_000, 500):
        wm.update(now_ms)
        if carrier.transport_task is None and carrier.carrying is None:
            break

    assert sawmill.input_amount() == sawmill.input_capacity()
    assert town_hall.warehouse_amount("wood") == 1


def test_next_transport_task_picks_highest_priority_available_task_first() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    camp_a = registry.place(LumberCamp, near_town_hall_tile(8, 8))
    camp_b = registry.place(LumberCamp, near_town_hall_tile(12, 12))
    wm = WorkerManager(registry)
    camp_a.add_to_storage(1)
    camp_b.add_to_storage(1)
    wm.enqueue_transport_task(resource="wood", source=camp_a, target=town_hall, amount=1, priority=0)
    wm.enqueue_transport_task(resource="wood", source=camp_b, target=town_hall, amount=1, priority=10)

    picked = wm._next_transport_task()

    assert picked is not None
    assert picked.source is camp_b
    assert picked.priority == 10


def test_update_auto_enqueues_construction_tasks_from_town_hall() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    camp = registry.place(LumberCamp, near_town_hall_tile(8, 8))
    camp.construction_site = ConstructionSite(
        required_resources={"wood": 1},
        delivered_resources={},
        build_time_ms=10_000,
        build_started_ms=None,
        builder=None,
        target_level=1,
    )
    town_hall.add_to_warehouse("wood", 1)
    wm = WorkerManager(registry)

    wm.update(0)
    picked = wm._next_transport_task()

    assert picked is not None
    assert picked.source is town_hall
    assert picked.target is camp
    assert picked.resource == "wood"
    assert picked.priority == 10
    assert picked.purpose == "construction"


def test_carrier_delivery_to_construction_site_increments_delivered_resources() -> None:
    world = World(world_seed=2)
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    camp = registry.place(LumberCamp, near_town_hall_tile(8, 8))
    camp.construction_site = ConstructionSite(
        required_resources={"wood": 1},
        delivered_resources={},
        build_time_ms=10_000,
        build_started_ms=None,
        builder=None,
        target_level=1,
    )
    town_hall.add_to_warehouse("wood", 1)
    wm = WorkerManager(registry, now_ms_fn=lambda: 0)
    carrier = wm.hire("CARRIER")
    assert carrier is not None

    for now_ms in range(0, 120_000, 500):
        wm.update(now_ms)
        site = camp.construction_site
        if site is not None and int(site.delivered_resources.get("wood", 0)) >= 1:
            break

    site = camp.construction_site
    assert site is not None
    assert int(site.delivered_resources.get("wood", 0)) == 1
    assert site.is_fully_supplied()


def test_stale_construction_task_is_dropped_if_need_already_satisfied_before_pickup() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    camp = registry.place(LumberCamp, near_town_hall_tile(8, 8))
    camp.construction_site = ConstructionSite(
        required_resources={"wood": 1},
        delivered_resources={"wood": 1},
        build_time_ms=10_000,
        build_started_ms=None,
        builder=None,
        target_level=1,
    )
    source = registry.place(LumberCamp, near_town_hall_tile(14, 8))
    source.construction_site = None
    source.add_to_storage(1)
    wm = WorkerManager(registry, now_ms_fn=lambda: 0)
    carrier = wm.hire("CARRIER")
    assert carrier is not None
    wm.enqueue_transport_task(resource="wood", source=source, target=camp, amount=1, priority=10)
    wm.update(0)

    site = camp.construction_site
    assert site is not None
    assert int(site.delivered_resources.get("wood", 0)) == 1
    assert town_hall.warehouse_amount("wood") == 0
    assert source.stored == 1
    assert carrier.transport_task is None


def test_unavailable_construction_task_stays_queued_until_stock_appears() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    camp = registry.place(LumberCamp, near_town_hall_tile(8, 8))
    camp.construction_site = ConstructionSite(
        required_resources={"stone": 1},
        delivered_resources={},
        build_time_ms=10_000,
        build_started_ms=None,
        builder=None,
        target_level=1,
    )
    wm = WorkerManager(registry, now_ms_fn=lambda: 0)
    carrier = wm.hire("CARRIER")
    assert carrier is not None
    wm.enqueue_transport_task(
        resource="stone",
        source=town_hall,
        target=camp,
        amount=1,
        priority=10,
    )

    # Simulate a picked task that becomes unavailable at load time.
    task = wm._transport_queue.pop(0)
    carrier.transport_task = task
    carrier.state = "carrier_loading"
    carrier.camp_wait_until_ms = 0

    wm.update(0)

    assert carrier.transport_task is None
    assert carrier.state == "idle"
    assert any(t.resource == "stone" and t.target is camp for t in wm._transport_queue)

    town_hall.add_to_warehouse("stone", 1)
    for now_ms in range(1_000, 120_000, 500):
        wm.update(now_ms)
        site = camp.construction_site
        if site is not None and int(site.delivered_resources.get("stone", 0)) >= 1:
            break

    site = camp.construction_site
    assert site is not None
    assert int(site.delivered_resources.get("stone", 0)) == 1


def test_gatherer_deposit_routes_transport_to_construction_need_before_town_hall() -> None:
    now_ms = [0]
    world = World(world_seed=2)
    world._trees.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    camp = registry.place(LumberCamp, near_town_hall_tile(8, 8))
    target = registry.place(LumberCamp, near_town_hall_tile(14, 8))
    target.construction_site = ConstructionSite(
        required_resources={"wood": 1},
        delivered_resources={},
        build_time_ms=10_000,
        build_started_ms=None,
        builder=None,
        target_level=1,
    )
    camp.construction_site = None
    gx, gy = camp.grid_pos  # type: ignore[assignment]
    world._trees[(gx + 3, gy)] = Tree(stage=TreeStage.ADULT)  # noqa: SLF001
    wm = WorkerManager(registry, now_ms_fn=lambda: now_ms[0])
    lumberjack = wm.hire("LUMBERJACK")
    assert lumberjack is not None
    wm.reassign_all()

    now_ms[0] += 120_000
    wm.update(now_ms[0])
    now_ms[0] += CHOP_DURATION_MS
    wm.update(now_ms[0])
    now_ms[0] += 120_000
    wm.update(now_ms[0])
    wm.update(now_ms[0] + 1)

    task = wm._next_transport_task()
    assert task is not None
    assert task.source is camp
    assert task.target is target
    assert task.priority == 10


def test_hire_stonecutter_requires_town_hall_level_3() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    wm = WorkerManager(registry)
    wheat_before = town_hall.warehouse_amount("wheat")
    assert wm.hire("STONECUTTER") is None
    assert town_hall.warehouse_amount("wheat") == wheat_before
    town_hall.level = 3
    assert wm.hire("STONECUTTER") is not None
    assert town_hall.warehouse_amount("wheat") == wheat_before


def test_hire_miner_requires_town_hall_level_5() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    wm = WorkerManager(registry)
    assert wm.hire("MINER") is None
    town_hall.level = 5
    assert wm.hire("MINER") is not None


def test_reassign_all_detours_around_alive_tree_tile() -> None:
    world = World(world_seed=0)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    camp = registry.place(LumberCamp, near_town_hall_tile(8, 8))
    camp.construction_site = None
    cx, cy = camp.grid_pos  # type: ignore[assignment]
    tree_tile = (cx - 2, cy)
    world._trees[tree_tile] = Tree(stage=TreeStage.ADULT)  # noqa: SLF001
    wm = WorkerManager(registry)
    w = Worker("LUMBERJACK", stand_tile=(cx - 10, cy))
    wm.add_worker(w)

    wm.reassign_all()

    assert w.assigned_building is camp
    assert w.path
    assert tree_tile not in w.path


def test_reassign_all_can_use_tile_after_tree_removed() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry.place(TownHall, town_hall_origin_tile())
    camp = registry.place(LumberCamp, near_town_hall_tile(8, 8))
    camp.construction_site = None
    cx, cy = camp.grid_pos  # type: ignore[assignment]
    tree_tile = (cx - 2, cy)
    world._trees[tree_tile] = Tree(stage=TreeStage.ADULT)  # noqa: SLF001
    wm = WorkerManager(registry)
    w = Worker("LUMBERJACK", stand_tile=(cx - 10, cy))
    wm.add_worker(w)

    wm.reassign_all()
    assert tree_tile not in w.path

    w.assigned_building = None
    w.idle = True
    w.state = "idle"
    w.path = []
    world.remove_tree(*tree_tile)
    wm.reassign_all()
    # After tree removal the worker can again walk toward the camp; tree target is
    # only picked once the lumberjack has actually reached the camp.
    assert w.target_tree is None
    assert not w.idle
    assert w.state == "moving"


def test_reassign_all_detours_around_alive_stone_tile() -> None:
    from game.stones import Stone

    world = World(world_seed=0)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    camp = registry.place(LumberCamp, near_town_hall_tile(8, 8))
    camp.construction_site = None
    cx, cy = camp.grid_pos  # type: ignore[assignment]
    stone_tile = (cx - 2, cy)
    world._stones[stone_tile] = Stone()  # noqa: SLF001
    wm = WorkerManager(registry)
    w = Worker("LUMBERJACK", stand_tile=(cx - 10, cy))
    wm.add_worker(w)

    wm.reassign_all()

    assert w.assigned_building is camp
    assert w.path
    assert stone_tile not in w.path
