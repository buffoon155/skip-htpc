from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from skip_htpc.config import (
    app_by_id,
    app_order,
    default_config,
    load_config,
    validate_config,
)


class ConfigTests(unittest.TestCase):
    def test_defaults_are_the_three_apps(self) -> None:
        config = default_config()
        validate_config(config)
        self.assertEqual(app_order(config), ["kodi", "netflix", "areena"])
        self.assertEqual(app_by_id(config, "netflix")["url"], "https://www.netflix.com/browse")
        self.assertTrue(app_by_id(config, "areena")["url"].startswith("https://areena.yle.fi"))

    def test_override_replaces_browser_and_keeps_apps(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            path.write_text(json.dumps({"browser": "/usr/bin/chromium"}), encoding="utf-8")
            config = load_config([path])
        self.assertEqual(config["browser"], "/usr/bin/chromium")
        self.assertEqual(app_order(config), ["kodi", "netflix", "areena"])

    def test_http_url_is_rejected(self) -> None:
        config = default_config()
        config["apps"][1]["url"] = "http://www.netflix.com/browse"
        with self.assertRaises(ValueError):
            validate_config(config)

    def test_unknown_app(self) -> None:
        with self.assertRaises(KeyError):
            app_by_id(default_config(), "lounge")


if __name__ == "__main__":
    unittest.main()
