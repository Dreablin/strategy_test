"""Worker characteristic multipliers with permanent and temporary bonuses."""

from __future__ import annotations

from collections.abc import Hashable

_KINDS = ("move_speed_mult", "gather_speed_mult")
_MIN_MULT = 0.10


class Characteristics:
    """Tracks additive deltas and exposes clamped effective multipliers."""

    __slots__ = ("_permanent", "_temporary")

    def __init__(self) -> None:
        self._permanent: dict[tuple[Hashable, str], float] = {}
        self._temporary: list[tuple[str, float, int]] = []

    @property
    def move_speed_mult(self) -> float:
        return self._effective("move_speed_mult")

    @property
    def gather_speed_mult(self) -> float:
        return self._effective("gather_speed_mult")

    def add_permanent(self, source: Hashable, kind: str, value: float) -> None:
        self._validate_kind(kind)
        self._permanent[(source, kind)] = float(value)

    def remove_source(self, source: Hashable) -> None:
        keys = [key for key in self._permanent if key[0] == source]
        for key in keys:
            self._permanent.pop(key, None)

    def add_temporary(self, kind: str, value: float, expires_at_ms: int) -> None:
        self._validate_kind(kind)
        self._temporary.append((kind, float(value), int(expires_at_ms)))

    def tick(self, now_ms: int) -> None:
        now = int(now_ms)
        self._temporary = [entry for entry in self._temporary if entry[2] > now]

    def _effective(self, kind: str) -> float:
        base = 1.0
        perm = sum(v for (_source, k), v in self._permanent.items() if k == kind)
        temp = sum(v for (k, v, _exp) in self._temporary if k == kind)
        return max(_MIN_MULT, base + perm + temp)

    @staticmethod
    def _validate_kind(kind: str) -> None:
        if kind not in _KINDS:
            raise ValueError(f"unknown characteristic kind: {kind}")
