"""Worker manager: hire, reassign, demolition (PRD F-WORK / F-DEMO)."""

from game.buildings.farm import Farm
from game.buildings.iron_mine import IronMine
from game.buildings.lumber_camp import LumberCamp
from game.buildings.registry import BuildingRegistry
from game.buildings.school import School
from game.buildings.town_hall import TownHall
from game.characteristics import Characteristics
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.construction import ConstructionSite
from game.trees import Tree, TreeStage
from game.world import World
from game.workers import Worker, WorkerManager, building_center_tile, town_hall_spawn_tile


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


def test_assign_to_building_applies_level_bonus_source() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    camp = registry.place(LumberCamp, (10, 10))
    camp.level = 3
    wm = WorkerManager()
    worker = Worker("LUMBERJACK")
    wm.add_worker(worker)

    wm.assign_to_building(worker, camp)

    assert worker.characteristics.move_speed_mult == 1.10
    assert worker.characteristics.gather_speed_mult == 1.10


def test_notify_demolished_clears_building_level_bonus_source() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    camp = registry.place(LumberCamp, (12, 12))
    camp.level = 4
    wm = WorkerManager(registry=registry)
    worker = Worker("LUMBERJACK")
    wm.add_worker(worker)
    wm.assign_to_building(worker, camp)

    assert worker.characteristics.move_speed_mult == 1.15
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
    assert worker.characteristics.move_speed_mult == 1.05

    wm.assign_to_building(worker, camp_b)
    assert worker.characteristics.move_speed_mult == 1.20
    assert worker.characteristics.gather_speed_mult == 1.20


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
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    camp = registry.place(LumberCamp, (10, 10))
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
    assert camp.construction_site.builder is None

    wm.update(120_000)
    assert camp.construction_site is not None
    assert camp.construction_site.builder is builder
    assert camp.construction_site.build_started_ms == 120_000
    assert builder.state == "building"
    assert builder.current_tile == building_center_tile(camp)


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
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    camp1 = registry.place(LumberCamp, (8, 8))
    camp2 = registry.place(LumberCamp, near_town_hall_tile())
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
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    town_hall.level = 5
    registry.place(LumberCamp, (4, 4))
    farm = registry.place(Farm, near_town_hall_tile(12, 4))
    mine = registry.place(IronMine, (10, 20))
    wm = WorkerManager(registry)
    wm.add_worker(Worker("FARMER"))
    wm.reassign_all()
    assert wm.is_staffed(farm)
    assert not wm.is_staffed(mine)


def test_reassign_all_assigns_miner_to_empty_iron_mine() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    town_hall.level = 5
    registry.place(Farm, (4, 4))
    mine = registry.place(IronMine, near_town_hall_tile(12, 4))
    wm = WorkerManager(registry)
    wm.add_worker(Worker("MINER"))
    wm.reassign_all()
    assert wm.is_staffed(mine)


def test_reassign_all_sets_moving_path_to_reachable_approach_tile() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    camp = registry.place(LumberCamp, near_town_hall_tile(8, 8))
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
    registry = BuildingRegistry(world)
    town_hall = registry.place(TownHall, town_hall_origin_tile())
    town_hall.level = 5
    registry.place(IronMine, (26, 26))
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
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    camp = registry.place(LumberCamp, near_town_hall_tile(8, 8))
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


def test_demolish_moving_worker_becomes_idle_at_current_tile() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    camp = registry.place(LumberCamp, near_town_hall_tile(8, 8))
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


def test_reassign_all_does_not_retarget_worker_already_moving() -> None:
    world = World(world_seed=0)
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    camp_a = registry.place(LumberCamp, near_town_hall_tile())
    camp_b = registry.place(LumberCamp, near_town_hall_tile(15, 15))
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
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    camp = registry.place(LumberCamp, near_town_hall_tile(8, 8))
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
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    camp = registry.place(LumberCamp, near_town_hall_tile(8, 8))
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
    registry.place(TownHall, town_hall_origin_tile())
    camp = registry.place(LumberCamp, near_town_hall_tile(8, 8))
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
    registry = BuildingRegistry(world)
    registry.place(TownHall, town_hall_origin_tile())
    camp = registry.place(LumberCamp, near_town_hall_tile(8, 8))
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
