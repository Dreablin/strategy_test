"""Wall-clock tick scheduler for the fixed-length production cycle."""

from game.config import TICK_MS


class TickScheduler:
    """Fires at most once per `update` when `now_ms` reaches the next cycle boundary."""

    __slots__ = ("_next_tick_at",)

    def __init__(self) -> None:
        self._next_tick_at = TICK_MS

    def update(self, now_ms: int) -> bool:
        if now_ms < self._next_tick_at:
            return False
        self._next_tick_at = (now_ms // TICK_MS) * TICK_MS + TICK_MS
        return True
