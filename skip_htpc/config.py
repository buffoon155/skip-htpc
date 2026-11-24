from __future__ import annotations

import json
import os
from pathlib import Path


def default_config() -> dict:
    return {
        "browser": "",
        "audio_sink": "",
        "apps": [
            {
                "id": "kodi",
                "kind": "command",
                "command": ["kodi"],
                "class": "Kodi",
            },
            {
                "id": "youtube",
                "kind": "browser",
                "url": "https://www.youtube.com/tv",
                "class": "skip-htpc-youtube",
            },
            {
                "id": "areena",
                "kind": "browser",
                "url": "https://areena.yle.fi",
                "class": "skip-htpc-areena",
            },
            {
                "id": "netflix",
                "kind": "browser",
                "url": "https://www.netflix.com",
                "class": "skip-htpc-netflix",
            },
        ],
    }


def default_config_paths() -> list[Path]:
    paths: list[Path] = []
    system = Path("/etc/skip-htpc/config.json")
    if system.is_file():
        paths.append(system)
    xdg = os.environ.get("XDG_CONFIG_HOME")
    user_base = Path(xdg) if xdg else Path.home() / ".config"
    user = user_base / "skip-htpc" / "config.json"
    if user.is_file():
        paths.append(user)
    override = os.environ.get("SKIP_HTPC_CONFIG")
    if override:
        paths.append(Path(override))
    return paths


def merge_config(base: dict, override: dict) -> dict:
    merged = dict(base)
    for key, value in override.items():
        merged[key] = value
    return merged


def validate_config(config: dict) -> None:
    apps = config.get("apps")
    if not isinstance(apps, list) or not apps:
        raise ValueError("config apps must be a non-empty list")
    ids: list[str] = []
    for app in apps:
        if not isinstance(app, dict):
            raise ValueError("each app must be an object")
        app_id = app.get("id")
        kind = app.get("kind")
        wm_class = app.get("class")
        if not isinstance(app_id, str) or not app_id:
            raise ValueError("each app needs an id")
        if not isinstance(wm_class, str) or not wm_class:
            raise ValueError(f"{app_id} needs a window class")
        if kind == "browser":
            url = app.get("url")
            if not isinstance(url, str) or not url.startswith("https://"):
                raise ValueError(f"{app_id} needs an https url")
        elif kind == "command":
            command = app.get("command")
            if not isinstance(command, list) or not command or not all(
                isinstance(part, str) and part for part in command
            ):
                raise ValueError(f"{app_id} needs a command list")
        else:
            raise ValueError(f"{app_id} kind must be browser or command")
        ids.append(app_id)
    if len(ids) != len(set(ids)):
        raise ValueError("config app ids must be unique")


def load_config(paths: list[Path] | None = None) -> dict:
    config = default_config()
    for path in default_config_paths() if paths is None else paths:
        if not path.is_file():
            continue
        try:
            override = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path} is not valid JSON: {exc}") from exc
        if not isinstance(override, dict):
            raise ValueError(f"{path} must contain a JSON object")
        config = merge_config(config, override)
    validate_config(config)
    return config


def apply_url_override(app: dict) -> dict:
    """Honor SKIP_HTPC_<ID>_URL from launch.sh so config.yaml wins."""
    if app.get("kind") != "browser":
        return app
    url = os.environ.get(f"SKIP_HTPC_{str(app['id']).upper()}_URL", "").strip()
    if not url:
        return app
    if not url.startswith("https://"):
        raise ValueError(f"{app['id']} url override must be https")
    copied = dict(app)
    copied["url"] = url
    return copied


def app_order(config: dict) -> list[str]:
    return [app["id"] for app in config["apps"]]


def app_by_id(config: dict, app_id: str) -> dict:
    for app in config["apps"]:
        if app["id"] == app_id:
            return app
    known = ", ".join(app_order(config))
    raise KeyError(f"unknown app {app_id!r} (expected {known})")
