from __future__ import annotations

import re
from dataclasses import dataclass


_LINE = re.compile(
    r"^(0x[0-9a-fA-F]+)\s+(\S+)\s+(\S+)\s+(\S+)\s*(.*)$"
)


@dataclass(frozen=True)
class Window:
    id_hex: str
    desktop: str
    wm_class: str
    host: str
    title: str

    @property
    def id_int(self) -> int:
        return int(self.id_hex, 16)


def parse_wmctrl_lx(text: str) -> list[Window]:
    windows: list[Window] = []
    for line in text.splitlines():
        match = _LINE.match(line.strip())
        if not match:
            continue
        windows.append(
            Window(
                id_hex=match.group(1),
                desktop=match.group(2),
                wm_class=match.group(3),
                host=match.group(4),
                title=match.group(5),
            )
        )
    return windows


def class_parts(wm_class: str) -> set[str]:
    parts: set[str] = set()
    for token in wm_class.split():
        lowered = token.lower()
        parts.add(lowered)
        if "." in token:
            instance, _, klass = token.partition(".")
            parts.add(instance.lower())
            parts.add(klass.lower())
    return parts


def app_for_window(window: Window, config: dict) -> str | None:
    parts = class_parts(window.wm_class)
    for app in config["apps"]:
        if app["class"].lower() in parts:
            return app["id"]
    return None


def windows_for_app(windows: list[Window], config: dict, app_id: str) -> list[Window]:
    return [window for window in windows if app_for_window(window, config) == app_id]


def focused_app(
    windows: list[Window], active_id: int | None, config: dict
) -> str | None:
    if active_id is None:
        return None
    for window in windows:
        if window.id_int == active_id:
            return app_for_window(window, config)
    return None
