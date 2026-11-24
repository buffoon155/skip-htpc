from __future__ import annotations

from dataclasses import dataclass

from skip_htpc.windows import Window, windows_for_app


@dataclass(frozen=True)
class Plan:
    action: str
    app_id: str
    window_id: str | None


def plan_launch(app_id: str, windows: list[Window], config: dict) -> Plan:
    matches = windows_for_app(windows, config, app_id)
    if matches:
        return Plan("focus", app_id, matches[-1].id_hex)
    return Plan("spawn", app_id, None)


def cycle_target(
    active_app: str | None, last_app: str | None, order: list[str]
) -> str:
    if not order:
        raise ValueError("cycle order is empty")
    current = active_app if active_app in order else None
    if current is None and last_app in order:
        current = last_app
    if current is None:
        return order[0]
    index = order.index(current)
    return order[(index + 1) % len(order)]
