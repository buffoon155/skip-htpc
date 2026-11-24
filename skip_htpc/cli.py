from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from shutil import which

from skip_htpc.audio import pick_hdmi_sink
from skip_htpc.browser import resolve_browser, spawn_browser
from skip_htpc.config import app_by_id, app_order, apply_url_override, load_config
from skip_htpc.launch import cycle_target, plan_launch
from skip_htpc.nvidia import nvidia_status, nvidia_status_message
from skip_htpc.openbox_rc import ensure_cycle_keybind
from skip_htpc.paths import (
    debounce,
    extension_dir,
    log_line,
    profile_dir,
    read_last_app,
    write_last_app,
)
from skip_htpc.windows import focused_app, parse_wmctrl_lx

USAGE = """
usage: skip-htpc <command> [args]

commands:
  launch <app>          focus that app, or start it
  cycle                 focus the next app (bound to F13)
  audio                 use an HDMI PulseAudio or PipeWire sink
  which                 print the focused app id, or none
  apps                  print the cycle order
  doctor                check the browser, extension, and tools
  patch-openbox <file> insert the F13 keybind into an Openbox rc.xml
  nvidia-ok             installer check (see --help on that command)
  browser-supervise <app>
                        internal: start Chrome and hold its extension pipe

app ids come from the config. The defaults are kodi, netflix, areena.
""".strip()

WINDOW_WAIT_SECONDS = 8.0


class WindowQueryError(RuntimeError):
    pass


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in ("-h", "--help"):
        print(USAGE)
        return 0 if args else 2
    command, rest = args[0], args[1:]
    try:
        if command == "launch":
            return cmd_launch(rest)
        if command == "cycle":
            return cmd_cycle(rest)
        if command == "audio":
            return cmd_audio(rest)
        if command == "which":
            return cmd_which(rest)
        if command == "apps":
            return cmd_apps(rest)
        if command == "doctor":
            return cmd_doctor(rest)
        if command == "patch-openbox":
            return cmd_patch_openbox(rest)
        if command == "nvidia-ok":
            return cmd_nvidia_ok(rest)
        if command == "browser-supervise":
            return cmd_browser_supervise(rest)
    except WindowQueryError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except KeyError as exc:
        message = exc.args[0] if exc.args else str(exc)
        print(message, file=sys.stderr)
        return 2
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(USAGE, file=sys.stderr)
    return 2


def cmd_apps(args: list[str]) -> int:
    if args:
        print("apps takes no arguments", file=sys.stderr)
        return 2
    config = load_config()
    print(" ".join(app_order(config)))
    return 0


def cmd_which(args: list[str]) -> int:
    if args:
        print("which takes no arguments", file=sys.stderr)
        return 2
    config = load_config()
    windows = query_windows()
    active = focused_app(windows, active_window_id(), config)
    print(active or "none")
    return 0


def cmd_launch(args: list[str]) -> int:
    if len(args) != 1:
        print("usage: skip-htpc launch <app>", file=sys.stderr)
        return 2
    config = load_config()
    app = app_by_id(config, args[0])
    try:
        windows = query_windows()
    except WindowQueryError as exc:
        log_line(f"wmctrl unavailable ({exc}); starting {app['id']} anyway")
        windows = []
    plan = plan_launch(app["id"], windows, config)
    return _apply_plan(plan, config)


def cmd_cycle(args: list[str]) -> int:
    if args:
        print("cycle takes no arguments", file=sys.stderr)
        return 2
    if debounce("cycle", 0.35):
        return 0
    config = load_config()
    windows = query_windows()
    active = focused_app(windows, active_window_id(), config)
    target = cycle_target(active, read_last_app(), app_order(config))
    log_line(f"cycle active={active or 'none'} -> {target}")
    plan = plan_launch(target, windows, config)
    return _apply_plan(plan, config)


def _apply_plan(plan, config: dict) -> int:
    app = app_by_id(config, plan.app_id)
    if plan.action == "focus" and plan.window_id:
        focus_window(plan.window_id)
        write_last_app(plan.app_id)
        log_line(f"focus {plan.app_id} {plan.window_id}")
        return 0
    if not _spawn(app, config):
        return 1
    write_last_app(plan.app_id)
    log_line(f"spawn {plan.app_id}")
    found = _wait_for_app(plan.app_id, config, WINDOW_WAIT_SECONDS)
    if found is not None:
        focus_window(found.id_hex)
        log_line(f"focus {plan.app_id} {found.id_hex}")
    return 0


def _spawn(app: dict, config: dict) -> bool:
    app = apply_url_override(app)
    if app["kind"] == "command":
        try:
            subprocess.Popen(
                app["command"],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
        except FileNotFoundError:
            print(f"{app['command'][0]} is not installed", file=sys.stderr)
            return False
        return True
    binary = resolve_browser(config)
    if not binary:
        print("no Chrome or Chromium binary found", file=sys.stderr)
        return False
    manifest = extension_dir() / "manifest.json"
    if not manifest.is_file():
        print(f"extension manifest missing: {manifest}", file=sys.stderr)
        return False
    if os.environ.get("SKIP_HTPC_BROWSER_SUPERVISED") == "1":
        return _run_supervised_browser(app, config) == 0
    env = os.environ.copy()
    env["SKIP_HTPC_BROWSER_SUPERVISED"] = "1"
    log_path = profile_dir(app["id"]) / "supervisor.log"
    handle = log_path.open("ab")
    try:
        subprocess.Popen(
            [sys.executable, "-m", "skip_htpc", "browser-supervise", app["id"]],
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=handle,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    finally:
        handle.close()
    return True


def cmd_browser_supervise(args: list[str]) -> int:
    if len(args) != 1:
        print("usage: skip-htpc browser-supervise <app>", file=sys.stderr)
        return 2
    config = load_config()
    app = app_by_id(config, args[0])
    if app["kind"] != "browser":
        print(f"{app['id']} is not a browser app", file=sys.stderr)
        return 2
    return _run_supervised_browser(app, config)


def _run_supervised_browser(app: dict, config: dict) -> int:
    binary = resolve_browser(config)
    if not binary:
        print("no Chrome or Chromium binary found", file=sys.stderr)
        return 1
    extension = extension_dir()
    manifest = extension / "manifest.json"
    if not manifest.is_file():
        print(f"extension manifest missing: {manifest}", file=sys.stderr)
        return 1
    data_dir = profile_dir(app["id"])
    log_line(f"browser {app['id']} via {binary}")
    session = spawn_browser(binary, app, extension, data_dir)
    proc = session if isinstance(session, subprocess.Popen) else session.proc
    if not isinstance(session, subprocess.Popen):
        response = session.cdp_response
        if response is None:
            log_line(f"extension load for {app['id']} produced no CDP response")
        elif "error" in response:
            log_line(f"extension load for {app['id']} failed: {response['error']}")
        else:
            log_line(f"extension loaded for {app['id']}")
    code = proc.wait()
    if not isinstance(session, subprocess.Popen):
        session.close()
    return int(code) if code is not None else 0


def cmd_audio(args: list[str]) -> int:
    if args:
        print("audio takes no arguments", file=sys.stderr)
        return 2
    config = load_config()
    try:
        completed = subprocess.run(
            ["pactl", "list", "short", "sinks"],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except FileNotFoundError:
        print("pactl is not installed", file=sys.stderr)
        return 1
    except subprocess.TimeoutExpired:
        print("pactl timed out", file=sys.stderr)
        return 1
    if completed.returncode != 0:
        print(completed.stderr.strip() or "pactl list sinks failed", file=sys.stderr)
        return 1
    sink = pick_hdmi_sink(completed.stdout, str(config.get("audio_sink") or ""))
    if not sink:
        print("no HDMI sink found; leaving the default audio device", file=sys.stderr)
        return 0
    set_default = subprocess.run(
        ["pactl", "set-default-sink", sink],
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
    if set_default.returncode != 0:
        print(set_default.stderr.strip() or "could not set the default sink", file=sys.stderr)
        return 1
    log_line(f"audio sink {sink}")
    print(sink)
    return 0


def cmd_doctor(args: list[str]) -> int:
    if args:
        print("doctor takes no arguments", file=sys.stderr)
        return 2
    config = load_config()
    ok = True
    manifest_path = extension_dir() / "manifest.json"
    good, detail = extension_manifest_ok(manifest_path)
    print(f"extension: {'ok' if good else 'MISSING'} {detail}")
    ok = ok and good
    binary = resolve_browser(config)
    if binary:
        print(f"browser: {binary}")
    else:
        print("browser: MISSING (install google-chrome-stable or chromium)")
        ok = False
    for tool in ("wmctrl", "xdotool", "kodi", "pactl"):
        found = shutil_which(tool)
        print(f"{tool}: {found or 'MISSING'}")
        if tool == "wmctrl" and not found:
            ok = False
    gpu = _lspci_vga()
    if gpu:
        print(f"gpu: {gpu}")
    return 0 if ok else 1


def extension_manifest_ok(path: Path) -> tuple[bool, str]:
    if not path.is_file():
        return False, str(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return False, f"invalid JSON ({exc})"
    if data.get("manifest_version") != 3:
        return False, "manifest_version is not 3"
    scripts = data.get("content_scripts") or []
    matches: list[str] = []
    for script in scripts:
        matches.extend(script.get("matches") or [])
    needed = ("https://www.netflix.com/*", "https://areena.yle.fi/*")
    missing = [item for item in needed if item not in matches]
    if missing:
        return False, "missing host matches: " + ", ".join(missing)
    return True, str(data.get("name") or path.name)


def cmd_patch_openbox(args: list[str]) -> int:
    if len(args) != 1:
        print("usage: skip-htpc patch-openbox <rc.xml>", file=sys.stderr)
        return 2
    path = Path(args[0])
    text = path.read_text(encoding="utf-8")
    path.write_text(ensure_cycle_keybind(text), encoding="utf-8")
    print(path)
    return 0


def cmd_nvidia_ok(args: list[str]) -> int:
    version = ""
    depends = ""
    kernel = ""
    index = 0
    while index < len(args):
        flag = args[index]
        if flag in ("-h", "--help"):
            print(
                "usage: skip-htpc nvidia-ok --version VER --depends TEXT --kernel RELEASE",
                file=sys.stderr,
            )
            return 0
        if index + 1 >= len(args):
            print(f"{flag} needs a value", file=sys.stderr)
            return 2
        value = args[index + 1]
        if flag == "--version":
            version = value
        elif flag == "--depends":
            depends = value
        elif flag == "--kernel":
            kernel = value
        else:
            print(f"unknown flag {flag}", file=sys.stderr)
            return 2
        index += 2
    if not kernel:
        print("nvidia-ok needs --kernel", file=sys.stderr)
        return 2
    code = nvidia_status(version, depends, kernel)
    print(nvidia_status_message(code), file=sys.stderr)
    return code


def query_windows():
    try:
        completed = subprocess.run(
            ["wmctrl", "-lx"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except FileNotFoundError as exc:
        raise WindowQueryError("wmctrl is not installed") from exc
    except subprocess.TimeoutExpired as exc:
        raise WindowQueryError("wmctrl timed out") from exc
    if completed.returncode != 0:
        detail = completed.stderr.strip() or f"exit {completed.returncode}"
        raise WindowQueryError(f"wmctrl failed: {detail}")
    return parse_wmctrl_lx(completed.stdout)


def active_window_id() -> int | None:
    try:
        completed = subprocess.run(
            ["xdotool", "getactivewindow"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0:
        return None
    text = completed.stdout.strip()
    if not text.isdigit():
        return None
    return int(text)


def focus_window(window_id: str) -> None:
    completed = subprocess.run(
        ["wmctrl", "-ia", window_id],
        check=False,
        capture_output=True,
        text=True,
        timeout=5,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or f"exit {completed.returncode}"
        raise WindowQueryError(f"could not focus {window_id}: {detail}")


def _wait_for_app(app_id: str, config: dict, timeout: float):
    deadline = time.monotonic() + timeout
    while True:
        try:
            windows = query_windows()
        except WindowQueryError:
            windows = []
        plan = plan_launch(app_id, windows, config)
        if plan.action == "focus":
            matches = [
                window
                for window in windows
                if window.id_hex == plan.window_id
            ]
            if matches:
                return matches[0]
        if time.monotonic() >= deadline:
            return None
        time.sleep(0.2)


def shutil_which(name: str) -> str | None:
    return which(name)


def _lspci_vga() -> str:
    try:
        completed = subprocess.run(
            ["lspci"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return ""
    if completed.returncode != 0:
        return ""
    for line in completed.stdout.splitlines():
        if "VGA" in line or "3D" in line or "Display" in line:
            return line.strip()
    return ""
