"""Worker satiety: max storage, per-second drain, drift-free whole-second steps."""

from __future__ import annotations

from game.config import MAX_WORKER_SATIETY, SATIETY_DRAIN_PER_GAME_SECOND


def clamp_worker_satiety(value: int) -> int:
    """Clamp satiety to ``[0, MAX_WORKER_SATIETY]``."""
    v = int(value)
    if v <= 0:
        return 0
    if v >= MAX_WORKER_SATIETY:
        return MAX_WORKER_SATIETY
    return v


def apply_satiety_game_time(satiety: int, last_ms: int, now_ms: int) -> tuple[int, int]:
    """Apply drain for whole elapsed seconds between game clock samples.

    Returns ``(new_satiety, new_last_ms)`` where ``new_last_ms`` advances only by
    full seconds so fractional leftovers do not drift across frames.
    """
    now_ms = int(now_ms)
    last_ms = int(last_ms)
    if now_ms < last_ms:
        return clamp_worker_satiety(satiety), now_ms
    delta_ms = now_ms - last_ms
    whole_seconds = delta_ms // 1000
    new_last = last_ms + whole_seconds * 1000
    drained = whole_seconds * SATIETY_DRAIN_PER_GAME_SECOND
    return clamp_worker_satiety(satiety - drained), new_last
