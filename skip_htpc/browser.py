from __future__ import annotations

import json
import os
import queue
import shutil
import subprocess
import threading
import time
from dataclasses import dataclass
from pathlib import Path

# Branded Chrome dropped --load-extension in Chrome 137. The supported
# replacement is Extensions.loadUnpacked on the remote-debugging pipe.
# The pipe stays open for the life of the browser so a full devtools
# buffer cannot stall the renderer.

BROWSER_CANDIDATES = (
    "google-chrome-stable",
    "google-chrome",
    "chromium",
    "chromium-browser",
)

CDP_TIMEOUT_SECONDS = 5.0


def resolve_browser(config: dict, which=shutil.which) -> str | None:
    configured = str(config.get("browser") or "").strip()
    if configured:
        return configured
    for name in BROWSER_CANDIDATES:
        found = which(name)
        if found:
            return found
    return None


def uses_debugging_pipe(binary: str, version_text: str) -> bool:
    base = os.path.basename(binary).lower()
    first = version_text.strip().splitlines()[0].lower() if version_text.strip() else ""
    if "chromium" in base or first.startswith("chromium"):
        return False
    if "google-chrome" in base or first.startswith("google chrome"):
        return True
    return False


def browser_version(binary: str) -> str:
    try:
        completed = subprocess.run(
            [binary, "--version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return (completed.stdout or completed.stderr or "").strip()


def browser_argv(
    binary: str,
    app: dict,
    extension: Path,
    user_data_dir: Path,
    pipe: bool,
) -> list[str]:
    argv = [
        binary,
        f"--app={app['url']}",
        f"--user-data-dir={user_data_dir}",
        f"--class={app['class']}",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-session-crashed-bubble",
        "--disable-infobars",
        "--autoplay-policy=no-user-gesture-required",
        "--disable-features=Translate,MediaRouter",
        "--enable-features=AcceleratedVideoDecodeLinuxGL,AcceleratedVideoDecodeLinuxZeroCopyGL",
        "--use-gl=desktop",
        "--password-store=basic",
        "--start-maximized",
    ]
    if pipe:
        argv.extend(
            ["--remote-debugging-pipe", "--enable-unsafe-extension-debugging"]
        )
    else:
        argv.append(f"--load-extension={extension}")
    return argv


def encode_cdp(message: dict) -> bytes:
    return json.dumps(message, separators=(",", ":")).encode("utf-8") + b"\0"


def pop_cdp_messages(buffer: bytearray) -> list[dict]:
    messages: list[dict] = []
    while True:
        index = buffer.find(b"\0")
        if index < 0:
            break
        raw = bytes(buffer[:index])
        del buffer[: index + 1]
        if raw.strip():
            messages.append(json.loads(raw.decode("utf-8")))
    return messages


def load_unpacked_request(extension: Path, message_id: int = 1) -> dict:
    return {
        "id": message_id,
        "method": "Extensions.loadUnpacked",
        "params": {"path": str(extension)},
    }


@dataclass
class BrowserSession:
    proc: subprocess.Popen
    command_w: int
    response_r: int
    cdp_response: dict | None
    _thread: threading.Thread

    def close(self) -> None:
        for fd in (self.command_w, self.response_r):
            try:
                os.close(fd)
            except OSError:
                pass
        self._thread.join(timeout=1)


def _drain_responses(response_r: int, found: queue.Queue) -> None:
    buffer = bytearray()
    while True:
        try:
            chunk = os.read(response_r, 65536)
        except OSError:
            found.put(None)
            return
        if not chunk:
            found.put(None)
            return
        buffer.extend(chunk)
        try:
            for message in pop_cdp_messages(buffer):
                found.put(message)
        except json.JSONDecodeError:
            found.put(None)
            return
        if len(buffer) > 1_000_000:
            del buffer[:-65536]


def spawn_piped(
    argv: list[str],
    extension: Path,
    env: dict | None = None,
    log_path: Path | None = None,
    timeout: float = CDP_TIMEOUT_SECONDS,
) -> BrowserSession:
    command_r, command_w = os.pipe()
    response_r, response_w = os.pipe()
    for fd in (command_r, command_w, response_r, response_w):
        os.set_inheritable(fd, True)

    def preexec() -> None:
        os.dup2(command_r, 3)
        os.dup2(response_w, 4)
        for fd in (command_r, command_w, response_r, response_w):
            if fd > 4:
                os.close(fd)

    log_handle = None
    stdout = subprocess.DEVNULL
    if log_path is not None:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_handle = open(log_path, "ab")
        stdout = log_handle
    try:
        proc = subprocess.Popen(
            argv,
            stdin=subprocess.DEVNULL,
            stdout=stdout,
            stderr=subprocess.STDOUT,
            env=env,
            pass_fds=(command_r, command_w, response_r, response_w),
            preexec_fn=preexec,
            start_new_session=True,
        )
    finally:
        if log_handle is not None:
            log_handle.close()
        os.close(command_r)
        os.close(response_w)

    found: queue.Queue = queue.Queue()
    thread = threading.Thread(
        target=_drain_responses, args=(response_r, found), daemon=True
    )
    thread.start()
    try:
        os.write(command_w, encode_cdp(load_unpacked_request(extension)))
    except OSError:
        proc.kill()
        raise

    response = _wait_for_id(found, 1, timeout)
    return BrowserSession(proc, command_w, response_r, response, thread)


def _wait_for_id(found: queue.Queue, message_id: int, timeout: float) -> dict | None:
    deadline = time.monotonic() + timeout
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return None
        try:
            message = found.get(timeout=remaining)
        except queue.Empty:
            return None
        if message is None:
            return None
        if message.get("id") == message_id:
            return message


def spawn_browser(
    binary: str,
    app: dict,
    extension: Path,
    user_data_dir: Path,
    env: dict | None = None,
) -> subprocess.Popen | BrowserSession:
    version = browser_version(binary)
    pipe = uses_debugging_pipe(binary, version)
    argv = browser_argv(binary, app, extension, user_data_dir, pipe)
    child_env = os.environ.copy() if env is None else dict(env)
    # Mesa's VA-API driver for the RX 580. Chrome and the page decode with it.
    child_env.setdefault("LIBVA_DRIVER_NAME", "radeonsi")
    if pipe:
        return spawn_piped(
            argv,
            extension,
            env=child_env,
            log_path=user_data_dir / "chrome.log",
        )
    return subprocess.Popen(
        argv,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=child_env,
        start_new_session=True,
    )
