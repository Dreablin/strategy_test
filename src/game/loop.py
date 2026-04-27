"""Production loop helpers."""

from game.buildings.registry import BuildingRegistry
from game.resources import ResourceManager
from game.workers import WorkerManager


def apply_production_tick(
    registry: BuildingRegistry, resources: ResourceManager, workers: WorkerManager
) -> None:
    """Apply one 10-second production cycle from working buildings only."""
    placed = set(registry.all())
    for building in workers.working_buildings():
        if building not in placed:
            continue
        if hasattr(building, "is_storage_full") and building.is_storage_full():
            continue
        income = type(building).income(building.level)
        if not income:
            # Active-cycle buildings (e.g., Lumber Camp) deposit via worker logic.
            continue
        for name, amount in income.items():
            resources.add(name, amount)
