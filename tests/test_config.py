from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import os
from unittest import mock

from skip_htpc.config import (
    app_by_id,
    app_order,
    apply_url_override,
    default_config,
    load_config,
    validate_config,
)


class ConfigTests(unittest.TestCase):
    def test_defaults_are_kodi_youtube_areena_and_netflix(self) -> None:
        config = default_config()
        validate_config(config)
        self.assertEqual(app_order(config), ["kodi", "youtube", "areena", "netflix"])
        self.assertEqual(app_by_id(config, "youtube")["url"], "https://www.youtube.com/tv")
        self.assertEqual(app_by_id(config, "areena")["url"], "https://areena.yle.fi")
        self.assertEqual(app_by_id(config, "netflix")["url"], "https://www.netflix.com")

    def test_override_replaces_browser_and_keeps_apps(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            path.write_text(json.dumps({"browser": "/usr/bin/chromium"}), encoding="utf-8")
            config = load_config([path])
        self.assertEqual(config["browser"], "/usr/bin/chromium")
        self.assertEqual(app_order(config), ["kodi", "youtube", "areena", "netflix"])

    def test_http_url_is_rejected(self) -> None:
        config = default_config()
        app_by_id(config, "netflix")["url"] = "http://www.netflix.com"
        with self.assertRaises(ValueError):
            validate_config(config)

    def test_launch_script_can_override_the_browser_url(self) -> None:
        app = app_by_id(default_config(), "netflix")
        with mock.patch.dict(os.environ, {"SKIP_HTPC_NETFLIX_URL": "https://www.netflix.com"}):
            self.assertEqual(apply_url_override(app)["url"], "https://www.netflix.com")
        with mock.patch.dict(os.environ, {"SKIP_HTPC_NETFLIX_URL": "http://www.netflix.com"}):
            with self.assertRaises(ValueError):
                apply_url_override(app)

    def test_unknown_app(self) -> None:
        with self.assertRaises(KeyError):
            app_by_id(default_config(), "lounge")


if __name__ == "__main__":
    unittest.main()
