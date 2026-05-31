"""Shared i18n helpers for building sub-panels."""

from __future__ import annotations

from game import i18n
from game.resource_catalog import resource_display_label
from game.worker_status import localized_status

_BLOCKED_REASON_IDS: dict[str, str] = {
    "no worker": "no_worker",
    "inactive": "inactive",
    "resting": "resting",
    "output full": "output_full",
    "storage full": "storage_full",
    "no wood": "no_wood",
    "no wheat": "no_wheat",
    "no flour": "no_flour",
    "no water": "no_water",
    "no chicken": "no_chicken",
    "no bread": "no_bread",
    "no grain": "no_grain",
    "running": "processing",
}


def active_toggle_label(active: bool) -> str:
    return i18n.t("ui.common.active" if active else "ui.common.inactive")


def resource_amount_line(resource_key: str, amount: int, capacity: int) -> str:
    return i18n.t(
        "ui.panel.amount_line",
        label=resource_display_label(resource_key),
        amount=int(amount),
        capacity=int(capacity),
    )


def flow_line(*, role_key: str, resource_key: str, amount: int, capacity: int) -> str:
    return i18n.t(
        "ui.panel.flow_line",
        role=i18n.t(role_key),
        label=resource_display_label(resource_key),
        amount=int(amount),
        capacity=int(capacity),
    )


def blocked_line(reason_slug: str) -> str:
    status_id = _BLOCKED_REASON_IDS.get(reason_slug, reason_slug.replace(" ", "_"))
    return i18n.t("ui.panel.blocked_line", reason=localized_status(status_id))


def production_line(status_id: str | None) -> str:
    sid = status_id or "idle"
    return i18n.t("ui.panel.production_line", status=localized_status(sid))
