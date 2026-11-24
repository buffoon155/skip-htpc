from __future__ import annotations

import os
import sys
import time
from pathlib import Path


def share_root() -> Path:
    override = os.environ.get("SKIP_HTPC_SHARE")
    if override:
        return Path(override)
    return Path(__file__).resolve().parents[1]


def extension_dir() -> Path:
    override = os.environ.get("SKIP_HTPC_EXTENSION")
    if override:
        return Path(override)
    return share_root() / "extension"


def state_dir() -> Path:
    override = os.environ.get("SKIP_HTPC_STATE")
    if override:
        return Path(override)
    xdg = os.environ.get("XDG_STATE_HOME")
    base = Path(xdg) if xdg else Path.home() / ".local" / "state"
    return base / "skip-htpc"


def profile_root() -> Path:
    override = os.environ.get("SKIP_HTPC_PROFILES")
    if override:
        return Path(override)
    return Path.home() / ".local" / "share" / "skip-htpc" / "profiles"


def profile_dir(app_id: str) -> Path:
    path = profile_root() / app_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def read_last_app() -> str | None:
    path = state_dir() / "last-app"
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8").strip()
    return text or None


def write_last_app(app_id: str) -> None:
    directory = state_dir()
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "last-app").write_text(app_id + "\n", encoding="utf-8")


def debounce(name: str, interval: float) -> bool:
    """Return True when name was used less than interval seconds ago.

    The call that returns False records the current time. Held keys repeat
    faster than a person presses F13 twice, so the repeat is ignored.
    """
    directory = state_dir()
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"debounce-{name}"
    now = time.time()
    if path.is_file():
        try:
            previous = float(path.read_text(encoding="utf-8").strip() or "0")
        except ValueError:
            previous = 0.0
        if now - previous < interval:
            return True
    path.write_text(str(now), encoding="utf-8")
    return False


def log_line(message: str) -> None:
    directory = state_dir()
    directory.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with (directory / "launcher.log").open("a", encoding="utf-8") as handle:
        handle.write(f"{stamp} {message}\n")
    print(message, file=sys.stderr)
