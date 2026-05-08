"""RED tests for carrier inputs to canteen (T256).

Expect failures until T257 adds `canteen_input_transport_tasks`, canteen-local
chicken/bread acceptance from Town Hall, water intake compatible with
`water_input_transport_tasks`, and enqueue logic that respects inbound deliveries.
"""

from __future__ import annotations

from game.buildings.canteen import Canteen
from game.buildings.registry import BuildingRegistry
from game.buildings.town_hall import TownHall
from game.buildings.well import Well
from game.config import near_town_hall_tile, town_hall_origin_tile
from game.transport_tasks import water_input_transport_tasks
from game.world import World
from game.worker_models import TransportTask, Worker
from game.workers import WorkerManager


def _canteen_input_transport_tasks():
    import game.transport_tasks as tt

    assert hasattr(tt, "canteen_input_transport_tasks"), (
        "T257: define transport_tasks.canteen_input_transport_tasks(registry)"
    )
    return tt.canteen_input_transport_tasks


def _empty_world_registry_canteen_th_well() -> tuple[BuildingRegistry, TownHall, Canteen, Well]:
    world = World(world_seed=1)
    world._trees.clear()  # noqa: SLF001
    world._stones.clear()  # noqa: SLF001
    registry = BuildingRegistry(world)
    th = registry.place(TownHall, town_hall_origin_tile())
    canteen = registry.place(Canteen, near_town_hall_tile(12, 8))
    canteen.construction_site = None
    well = registry.place(Well, near_town_hall_tile(6, 8))
    well.construction_site = None
    return registry, th, canteen, well


def test_transport_tasks_exports_canteen_input_transport_tasks() -> None:
    _canteen_input_transport_tasks()


def test_canteen_input_tasks_deliver_chicken_and_bread_from_town_hall_when_space() -> None:
    canteen_input_transport_tasks = _canteen_input_transport_tasks()
    registry, th, canteen, _ = _empty_world_registry_canteen_th_well()
    th.add_to_warehouse("chicken", 10)
    th.add_to_warehouse("bread", 10)

    tasks = canteen_input_transport_tasks(registry)

    cap_c = canteen.local_storage_capacity("chicken")
    cap_b = canteen.local_storage_capacity("bread")
    ch = [t for t in tasks if t.resource == "chicken" and t.source is th and t.target is canteen]
    br = [t for t in tasks if t.resource == "bread" and t.source is th and t.target is canteen]
    assert len(ch) == cap_c
    assert len(br) == cap_b


def test_canteen_input_tasks_respect_existing_stock() -> None:
    canteen_input_transport_tasks = _canteen_input_transport_tasks()
    registry, th, canteen, _ = _empty_world_registry_canteen_th_well()
    th.add_to_warehouse("chicken", 10)
    th.add_to_warehouse("bread", 10)
    canteen.add_local_storage("chicken", 3)
    canteen.add_local_storage("bread", 2)

    tasks = canteen_input_transport_tasks(registry)

    cap_c = canteen.local_storage_capacity("chicken")
    cap_b = canteen.local_storage_capacity("bread")
    want_c = cap_c - 3
    want_b = cap_b - 2
    ch = [t for t in tasks if t.resource == "chicken" and t.source is th and t.target is canteen]
    br = [t for t in tasks if t.resource == "bread" and t.source is th and t.target is canteen]
    assert len(ch) == want_c
    assert len(br) == want_b


def test_canteen_input_tasks_skip_inactive_canteen() -> None:
    canteen_input_transport_tasks = _canteen_input_transport_tasks()
    registry, th, canteen, _ = _empty_world_registry_canteen_th_well()
    th.add_to_warehouse("chicken", 10)
    th.add_to_warehouse("bread", 10)
    canteen.set_active(False)

    tasks = canteen_input_transport_tasks(registry)

    assert not any(t.target is canteen for t in tasks)


def test_water_input_tasks_use_well_to_canteen_when_space() -> None:
    registry, _, canteen, well = _empty_world_registry_canteen_th_well()

    tasks = water_input_transport_tasks(registry)

    water_to_canteen = [
        t for t in tasks if t.resource == "water" and t.target is canteen and t.source.type_tag == "WELL"
    ]
    assert water_to_canteen, "canteen must accept well water like bakery (T257)"
    assert all(t.source is well for t in water_to_canteen)


def test_worker_manager_respects_inbound_water_cap_for_canteen() -> None:
    """Duplicate / in-flight water must not enqueue past local water capacity (mirrors bakery)."""
    registry, _, canteen, well = _empty_world_registry_canteen_th_well()
    cap = canteen.local_storage_capacity("water")
    canteen.add_local_storage("water", cap - 2)

    wm = WorkerManager(registry, now_ms_fn=lambda: 0)
    carrier = Worker("CARRIER")
    carrier.transport_task = TransportTask(resource="water", source=well, target=canteen)
    carrier.carrying = "water"
    wm.add_worker(carrier)

    wm.update(0)

    queued = [t for t in wm._transport_queue if t.resource == "water" and t.target is canteen]  # noqa: SLF001
    assert len(queued) == 1


def test_worker_manager_respects_inbound_chicken_for_canteen() -> None:
    """In-flight chicken must count against capacity when enqueueing refills (mirrors bakery water)."""
    registry, th, canteen, _ = _empty_world_registry_canteen_th_well()
    th.add_to_warehouse("chicken", 10)
    cap = canteen.local_storage_capacity("chicken")
    canteen.add_local_storage("chicken", cap - 2)

    wm = WorkerManager(registry, now_ms_fn=lambda: 0)
    carrier = Worker("CARRIER")
    carrier.transport_task = TransportTask(resource="chicken", source=th, target=canteen)
    carrier.carrying = "chicken"
    wm.add_worker(carrier)

    wm.update(0)

    queued = [t for t in wm._transport_queue if t.resource == "chicken" and t.target is canteen]  # noqa: SLF001
    assert len(queued) == 1
