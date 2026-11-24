from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

from skip_htpc.browser import (
    browser_argv,
    encode_cdp,
    load_unpacked_request,
    pop_cdp_messages,
    resolve_browser,
    spawn_piped,
    uses_debugging_pipe,
)
from skip_htpc.config import default_config


class BrowserArgTests(unittest.TestCase):
    def test_branded_chrome_uses_the_pipe(self) -> None:
        self.assertTrue(uses_debugging_pipe("google-chrome-stable", "Google Chrome 142.0.0.0"))
        self.assertTrue(uses_debugging_pipe("/usr/bin/google-chrome", ""))
        self.assertFalse(uses_debugging_pipe("chromium", "Chromium 142.0.0.0"))
        self.assertFalse(uses_debugging_pipe("chromium-browser", "Chromium 120.0"))

    def test_argv_splits_the_two_loading_methods(self) -> None:
        app = default_config()["apps"][1]
        extension = Path("/usr/local/share/skip-htpc/extension")
        profile = Path("/tmp/netflix-profile")
        piped = browser_argv("google-chrome-stable", app, extension, profile, True)
        plain = browser_argv("chromium", app, extension, profile, False)
        self.assertIn("--remote-debugging-pipe", piped)
        self.assertIn("--enable-unsafe-extension-debugging", piped)
        self.assertNotIn("--load-extension=" + str(extension), piped)
        self.assertIn(f"--load-extension={extension}", plain)
        self.assertNotIn("--remote-debugging-pipe", plain)
        self.assertIn("--app=https://www.netflix.com/browse", plain)
        self.assertIn("--class=skip-htpc-netflix", plain)
        self.assertIn(f"--user-data-dir={profile}", plain)

    def test_resolve_browser_prefers_config_then_chrome(self) -> None:
        config = default_config()
        config["browser"] = "/opt/chrome"
        self.assertEqual(resolve_browser(config, which=lambda name: None), "/opt/chrome")
        config["browser"] = ""
        seen: list[str] = []

        def which(name: str) -> str | None:
            seen.append(name)
            if name == "google-chrome-stable":
                return "/usr/bin/google-chrome-stable"
            return None

        self.assertEqual(resolve_browser(config, which=which), "/usr/bin/google-chrome-stable")
        self.assertEqual(seen[0], "google-chrome-stable")

    def test_cdp_framing(self) -> None:
        extension = Path("/opt/skip-htpc/extension")
        payload = encode_cdp(load_unpacked_request(extension, 7))
        self.assertTrue(payload.endswith(b"\0"))
        buffer = bytearray(payload + payload)
        messages = pop_cdp_messages(buffer)
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["method"], "Extensions.loadUnpacked")
        self.assertEqual(messages[0]["params"]["path"], str(extension))
        self.assertEqual(buffer, bytearray())


class BrowserPipeTests(unittest.TestCase):
    def test_fake_chrome_receives_load_unpacked(self) -> None:
        fake = Path(__file__).parent / "fake_chrome.py"
        with tempfile.TemporaryDirectory() as tmp:
            request_path = Path(tmp) / "request.json"
            extension = Path(tmp) / "extension"
            extension.mkdir()
            env = os.environ.copy()
            env["FAKE_CHROME_REQUEST"] = str(request_path)
            argv = [sys.executable, str(fake), "--app=https://www.netflix.com/browse"]
            session = spawn_piped(argv, extension, env=env, timeout=5)
            try:
                self.assertIsNotNone(session.cdp_response)
                assert session.cdp_response is not None
                self.assertEqual(session.cdp_response["result"]["id"], "fakedevextension")
                written = json.loads(request_path.read_text(encoding="utf-8"))
                self.assertEqual(written["method"], "Extensions.loadUnpacked")
                self.assertEqual(written["params"]["path"], str(extension))
                self.assertIsNone(session.proc.poll())
            finally:
                session.proc.kill()
                session.proc.wait(timeout=5)
                session.close()


if __name__ == "__main__":
    unittest.main()
