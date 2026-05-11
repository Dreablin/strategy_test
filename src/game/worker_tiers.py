"""Worker tier metadata: basic vs advanced."""

from __future__ import annotations

_WORKER_TIERS: dict[str, str] = {
    "LUMBERJACK": "basic",
    "STONECUTTER": "basic",
    "MINER": "basic",
    "FARMER": "basic",
    "ANIMAL_HERDER": "basic",
    "FORESTER": "basic",
    "SAWYER": "basic",
    "MILLER": "basic",
    "BAKER": "basic",
    "COOK": "basic",
    "WATERMAN": "basic",
    "CARRIER": "basic",
    "BUILDER": "basic",
}

ALL_TIERS: tuple[str, ...] = ("basic", "advanced")


def worker_tier(worker_type: str) -> str:
    """Return the tier id for *worker_type* (default ``'basic'``)."""
    return _WORKER_TIERS.get(worker_type, "basic")


def workers_of_tier(tier: str) -> list[str]:
    """Return all registered worker types belonging to *tier*."""
    return [wt for wt, t in _WORKER_TIERS.items() if t == tier]


def register_worker_tier(worker_type: str, tier: str) -> None:
    """Register or update the tier for a worker type."""
    if tier not in ALL_TIERS:
        raise ValueError(f"unknown tier {tier!r}; valid: {ALL_TIERS}")
    _WORKER_TIERS[worker_type] = tier
