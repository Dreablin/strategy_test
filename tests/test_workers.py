"""Worker manager: hire, reassign, demolition (PRD F-WORK / F-DEMO)."""

from game.buildings.farm import Farm
from game.buildings.iron_mine import IronMine
from game.buildings.lumber_camp import LumberCamp
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.config import WORKER_HIRE_COST
from game.resources import ResourceManager
from game.trees import Tree, TreeStage
from game.world import World
from game.workers import Worker, WorkerManager, building_center_tile, town_hall_spawn_tile


def test_building_center_tile_for_2x2() -> None:
    b = LumberCamp(level=1, grid_pos=(10, 8))
    assert building_center_tile(b) == (11, 9)


def test_demolition_parks_assigned_worker_on_center_tile() -> None:
    world = World()
    registry = BuildingRegistry(world)
    camp = registry.place(LumberCamp, (14, 14))
    wm = WorkerManager()
    w = Worker("LUMBERJACK")
    wm.add_worker(w)
    wm.assign_to_building(w, camp)
    assert not w.idle
    registry.demolish(camp, wm)
    assert w.idle
    assert w.assigned_building is None
    assert w.stand_tile == (15, 15)


def test_demolition_does_not_affect_other_workers() -> None:
    world = World()
    registry = BuildingRegistry(world)
    a = registry.place(LumberCamp, (5, 5))
    b = registry.place(LumberCamp, (20, 20))
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


def test_hire_deducts_50_food_and_returns_worker() -> None:
    world = World()
    registry = BuildingRegistry(world)
    resources = ResourceManager()
    town_hall = registry.place(TownHall, (16, 16))
    wm = WorkerManager(resources, registry)
    food_before = resources.get("food")
    w = wm.hire("LUMBERJACK")
    assert w is not None
    assert w.type_tag == "LUMBERJACK"
    assert w.current_tile == town_hall_spawn_tile(town_hall)
    assert resources.get("food") == food_before - WORKER_HIRE_COST["food"]


def test_hire_returns_none_when_insufficient_food_and_does_not_deduct() -> None:
    world = World()
    registry = BuildingRegistry(world)
    resources = ResourceManager()
    registry.place(TownHall, (16, 16))
    while resources.get("food") >= WORKER_HIRE_COST["food"]:
        assert resources.try_spend({"food": 1})
    food_before = resources.get("food")
    wm = WorkerManager(resources, registry)
    assert wm.hire("LUMBERJACK") is None
    assert resources.get("food") == food_before


def test_reassign_all_assigns_one_idle_lumberjack_to_empty_lumber_camp() -> None:
    world = World()
    registry = BuildingRegistry(world)
    resources = ResourceManager()
    registry.place(TownHall, (16, 16))
    camp = registry.place(LumberCamp, (10, 10))
    wm = WorkerManager(resources, registry)
    wm.add_worker(Worker("LUMBERJACK"))
    wm.reassign_all()
    assert wm.is_staffed(camp)
    w = wm.workers()[0]
    assert not w.idle
    assert w.assigned_building is camp


def test_reassign_all_does_not_assign_stonecutter_to_lumber_camp() -> None:
    world = World()
    registry = BuildingRegistry(world)
    resources = ResourceManager()
    registry.place(TownHall, (16, 16))
    registry.place(LumberCamp, (10, 10))
    wm = WorkerManager(resources, registry)
    w = Worker("STONECUTTER")
    wm.add_worker(w)
    wm.reassign_all()
    assert w.idle
    assert w.assigned_building is None


def test_demolish_then_reassign_moves_worker_to_new_matching_building() -> None:
    world = World()
    registry = BuildingRegistry(world)
    resources = ResourceManager()
    registry.place(TownHall, (16, 16))
    camp1 = registry.place(LumberCamp, (8, 8))
    camp2 = registry.place(LumberCamp, (22, 22))
    wm = WorkerManager(resources, registry)
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
    world = World()
    registry = BuildingRegistry(world)
    resources = ResourceManager()
    town_hall = registry.place(TownHall, (16, 16))
    town_hall.level = 5
    registry.place(LumberCamp, (4, 4))
    farm = registry.place(Farm, (24, 24))
    mine = registry.place(IronMine, (10, 20))
    wm = WorkerManager(resources, registry)
    wm.add_worker(Worker("FARMER"))
    wm.reassign_all()
    assert wm.is_staffed(farm)
    assert not wm.is_staffed(mine)


def test_reassign_all_assigns_miner_to_empty_iron_mine() -> None:
    world = World()
    registry = BuildingRegistry(world)
    resources = ResourceManager()
    town_hall = registry.place(TownHall, (16, 16))
    town_hall.level = 5
    registry.place(Farm, (4, 4))
    mine = registry.place(IronMine, (24, 24))
    wm = WorkerManager(resources, registry)
    wm.add_worker(Worker("MINER"))
    wm.reassign_all()
    assert wm.is_staffed(mine)


def test_reassign_all_sets_moving_path_to_reachable_approach_tile() -> None:
    world = World()
    registry = BuildingRegistry(world)
    resources = ResourceManager()
    registry.place(TownHall, (16, 16))
    camp = registry.place(LumberCamp, (24, 24))
    wm = WorkerManager(resources, registry)
    w = Worker("LUMBERJACK", stand_tile=(20, 20))
    wm.add_worker(w)

    wm.reassign_all()

    assert w.assigned_building is camp
    assert w.state == "moving"
    assert len(w.path) >= 2
    assert w.path[0] == (20, 20)
    end = w.path[-1]
    cx, cy = camp.grid_pos  # type: ignore[misc]
    cw, ch = type(camp).footprint
    assert not world.is_occupied(*end)
    assert max(
        max(cx - end[0], end[0] - (cx + cw - 1), 0),
        max(cy - end[1], end[1] - (cy + ch - 1), 0),
    ) == 1


def test_reassign_all_uses_current_time_for_move_start_no_first_frame_teleport() -> None:
    world = World()
    registry = BuildingRegistry(world)
    resources = ResourceManager()
    town_hall = registry.place(TownHall, (16, 16))
    town_hall.level = 5
    registry.place(IronMine, (26, 26))
    now_holder = {"t": 100_000}
    wm = WorkerManager(resources, registry, now_ms_fn=lambda: now_holder["t"])
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
    world = World()
    registry = BuildingRegistry(world)
    resources = ResourceManager()
    registry.place(TownHall, (16, 16))
    camp = registry.place(LumberCamp, (24, 24))
    for y in range(23, 27):
        for x in range(23, 27):
            if camp.grid_pos is not None and 24 <= x <= 25 and 24 <= y <= 25:
                continue
            world.mark_occupied(x, y, 1, 1)
    wm = WorkerManager(resources, registry)
    w = Worker("LUMBERJACK", stand_tile=(20, 20))
    wm.add_worker(w)

    wm.reassign_all()

    assert w.idle
    assert w.assigned_building is None
    assert w.state == "idle"


def test_working_buildings_excludes_moving_worker_until_arrival() -> None:
    world = World()
    registry = BuildingRegistry(world)
    resources = ResourceManager()
    registry.place(TownHall, (16, 16))
    camp = registry.place(LumberCamp, (24, 24))
    wm = WorkerManager(resources, registry)
    w = Worker("LUMBERJACK", stand_tile=(20, 20))
    wm.add_worker(w)
    wm.reassign_all()

    assert camp not in wm.working_buildings()
    wm.update(120_000)
    assert camp in wm.working_buildings()


def test_worker_status_for_building_reports_on_the_way_then_assigned() -> None:
    world = World()
    registry = BuildingRegistry(world)
    resources = ResourceManager()
    registry.place(TownHall, (16, 16))
    camp = registry.place(LumberCamp, (24, 24))
    wm = WorkerManager(resources, registry)
    w = Worker("LUMBERJACK", stand_tile=(20, 20))
    wm.add_worker(w)
    wm.reassign_all()

    assert wm.worker_status_for_building(camp) == "on the way"
    wm.update(120_000)
    assert wm.worker_status_for_building(camp) == "assigned"


def test_demolish_moving_worker_becomes_idle_at_current_tile() -> None:
    world = World()
    registry = BuildingRegistry(world)
    resources = ResourceManager()
    registry.place(TownHall, (16, 16))
    camp = registry.place(LumberCamp, (24, 24))
    wm = WorkerManager(resources, registry)
    w = Worker("LUMBERJACK", stand_tile=(20, 20))
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
    world = World()
    registry = BuildingRegistry(world)
    resources = ResourceManager()
    registry.place(TownHall, (16, 16))
    camp_a = registry.place(LumberCamp, (22, 22))
    camp_b = registry.place(LumberCamp, (26, 26))
    wm = WorkerManager(resources, registry)
    w = Worker("LUMBERJACK", stand_tile=(20, 20))
    wm.add_worker(w)
    wm.reassign_all()
    first_target = w.assigned_building
    assert first_target in {camp_a, camp_b}
    assert w.state == "moving"

    wm.reassign_all()
    assert w.assigned_building is first_target
    assert w.state == "moving"


def test_reassign_all_one_slot_two_workers_only_one_assigned() -> None:
    world = World()
    registry = BuildingRegistry(world)
    resources = ResourceManager()
    registry.place(TownHall, (16, 16))
    camp = registry.place(LumberCamp, (24, 24))
    wm = WorkerManager(resources, registry)
    w1 = Worker("LUMBERJACK", stand_tile=(20, 20))
    w2 = Worker("LUMBERJACK", stand_tile=(21, 20))
    wm.add_worker(w1)
    wm.add_worker(w2)

    wm.reassign_all()
    assigned = [w for w in (w1, w2) if w.assigned_building is camp]
    idle = [w for w in (w1, w2) if w.assigned_building is None and w.idle]
    assert len(assigned) == 1
    assert len(idle) == 1


def test_hire_unknown_worker_type_returns_none_and_keeps_resources() -> None:
    world = World()
    registry = BuildingRegistry(world)
    resources = ResourceManager()
    registry.place(TownHall, (16, 16))
    wm = WorkerManager(resources, registry)
    food_before = resources.get("food")
    assert wm.hire("WIZARD") is None
    assert resources.get("food") == food_before


def test_hire_stonecutter_requires_town_hall_level_3() -> None:
    world = World()
    registry = BuildingRegistry(world)
    resources = ResourceManager()
    town_hall = registry.place(TownHall, (16, 16))
    wm = WorkerManager(resources, registry)
    food_before = resources.get("food")
    assert wm.hire("STONECUTTER") is None
    assert resources.get("food") == food_before
    town_hall.level = 3
    assert wm.hire("STONECUTTER") is not None
    assert resources.get("food") == food_before - WORKER_HIRE_COST["food"]


def test_hire_miner_requires_town_hall_level_5() -> None:
    world = World()
    registry = BuildingRegistry(world)
    resources = ResourceManager()
    town_hall = registry.place(TownHall, (16, 16))
    wm = WorkerManager(resources, registry)
    assert wm.hire("MINER") is None
    town_hall.level = 5
    assert wm.hire("MINER") is not None


def test_reassign_all_detours_around_alive_tree_tile() -> None:
    world = World()
    registry = BuildingRegistry(world)
    resources = ResourceManager()
    registry.place(TownHall, (16, 16))
    camp = registry.place(LumberCamp, (24, 24))
    world._trees[(22, 22)] = Tree(stage=TreeStage.ADULT)  # noqa: SLF001
    wm = WorkerManager(resources, registry)
    w = Worker("LUMBERJACK", stand_tile=(20, 20))
    wm.add_worker(w)

    wm.reassign_all()

    assert w.assigned_building is camp
    assert w.path
    assert (22, 22) not in w.path


def test_reassign_all_can_use_tile_after_tree_removed() -> None:
    world = World()
    registry = BuildingRegistry(world)
    resources = ResourceManager()
    registry.place(TownHall, (16, 16))
    registry.place(LumberCamp, (24, 24))
    world._trees[(22, 22)] = Tree(stage=TreeStage.ADULT)  # noqa: SLF001
    wm = WorkerManager(resources, registry)
    w = Worker("LUMBERJACK", stand_tile=(20, 20))
    wm.add_worker(w)

    wm.reassign_all()
    assert (22, 22) not in w.path

    w.assigned_building = None
    w.idle = True
    w.state = "idle"
    w.path = []
    world.remove_tree(22, 22)
    wm.reassign_all()
    assert (22, 22) in w.path
