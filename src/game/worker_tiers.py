"""Worker tier metadata: basic vs advanced."""

from __future__ import annotations

from game.config import SETTINGS

ALL_TIERS: tuple[str, ...] = ("basic", "advanced")


def _configured_worker_tiers() -> dict[str, str]:
    payload = SETTINGS.get("workers", {}).get("tiers", {})
    if not isinstance(payload, dict):
        raise ValueError("workers.tiers must be an object")

    result: dict[str, str] = {}
    for worker_type, tier in payload.items():
        worker_key = str(worker_type).upper()
        tier_key = str(tier).lower()
        if tier_key not in ALL_TIERS:
            raise ValueError(f"unknown tier {tier_key!r} for worker {worker_key!r}; valid: {ALL_TIERS}")
        result[worker_key] = tier_key
    return result


_WORKER_TIERS: dict[str, str] = _configured_worker_tiers()


def worker_tier(worker_type: str) -> str:
    """Return the tier id for *worker_type* (default ``'basic'``)."""
    return _WORKER_TIERS.get(str(worker_type).upper(), "basic")


def workers_of_tier(tier: str) -> list[str]:
    """Return all registered worker types belonging to *tier*."""
    return [wt for wt, t in _WORKER_TIERS.items() if t == tier]


def register_worker_tier(worker_type: str, tier: str) -> None:
    """Register or update the tier for a worker type."""
    tier_key = str(tier).lower()
    if tier_key not in ALL_TIERS:
        raise ValueError(f"unknown tier {tier_key!r}; valid: {ALL_TIERS}")
    _WORKER_TIERS[str(worker_type).upper()] = tier_key
