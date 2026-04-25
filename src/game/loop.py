"""Production loop helpers."""

from game.buildings.registry import BuildingRegistry
from game.resources import ResourceManager
from game.workers import WorkerManager


def apply_production_tick(
    registry: BuildingRegistry, resources: ResourceManager, workers: WorkerManager
) -> None:
    """Apply one 10-second production cycle from staffed buildings only."""
    placed = set(registry.all())
    for building in workers.staffed_buildings():
        if building not in placed:
            continue
        for name, amount in type(building).income(building.level).items():
            resources.add(name, amount)
