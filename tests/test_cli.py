from __future__ import annotations

import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

from skip_htpc import cli
from skip_htpc.config import default_config
from skip_htpc.paths import debounce


class CliTests(unittest.TestCase):
    def test_help_and_apps(self) -> None:
        with redirect_stdout(io.StringIO()) as stdout:
            self.assertEqual(cli.main(["--help"]), 0)
        self.assertIn("cycle", stdout.getvalue())
        with mock.patch.object(cli, "load_config", default_config):
            with redirect_stdout(io.StringIO()) as stdout:
                self.assertEqual(cli.main(["apps"]), 0)
        self.assertEqual(stdout.getvalue().strip(), "kodi netflix areena")

    def test_launch_needs_an_app(self) -> None:
        with redirect_stderr(io.StringIO()):
            self.assertEqual(cli.main(["launch"]), 2)
        with redirect_stderr(io.StringIO()) as stderr:
            self.assertEqual(cli.main(["launch", "lounge"]), 2)
        self.assertIn("unknown app", stderr.getvalue())

    def test_nvidia_ok_command(self) -> None:
        with redirect_stderr(io.StringIO()):
            self.assertEqual(
                cli.main(
                    [
                        "nvidia-ok",
                        "--version",
                        "580.196.11-0ubuntu0.24.04.1",
                        "--depends",
                        "Depends: nvidia-dkms-580",
                        "--kernel",
                        "6.14.0-1-generic",
                    ]
                ),
                0,
            )
            self.assertEqual(
                cli.main(
                    [
                        "nvidia-ok",
                        "--version",
                        "580.196.11-0ubuntu1",
                        "--depends",
                        "Depends: nvidia-driver-590",
                        "--kernel",
                        "6.14.0-1-generic",
                    ]
                ),
                10,
            )

    def test_extension_manifest(self) -> None:
        root = Path(__file__).resolve().parents[1]
        ok, detail = cli.extension_manifest_ok(root / "extension" / "manifest.json")
        self.assertTrue(ok, detail)
        self.assertIn("spatial", detail.lower())

    def test_doctor_reports_a_missing_browser(self) -> None:
        with mock.patch.object(cli, "load_config", default_config):
            with mock.patch.object(cli, "resolve_browser", return_value=None):
                with mock.patch.object(cli, "shutil_which", return_value=None):
                    with mock.patch.object(cli, "_lspci_vga", return_value=""):
                        with redirect_stdout(io.StringIO()) as stdout:
                            code = cli.main(["doctor"])
        self.assertEqual(code, 1)
        text = stdout.getvalue()
        self.assertIn("extension: ok", text)
        self.assertIn("browser: MISSING", text)
        self.assertIn("wmctrl: MISSING", text)

    def test_cycle_debounce(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = os.environ.copy()
            env["SKIP_HTPC_STATE"] = tmp
            with mock.patch.dict(os.environ, env, clear=False):
                self.assertFalse(debounce("cycle", 0.35))
                self.assertTrue(debounce("cycle", 0.35))

    def test_bad_config_is_an_error(self) -> None:
        with mock.patch.object(
            cli,
            "load_config",
            side_effect=ValueError("config apps must be a non-empty list"),
        ):
            with redirect_stderr(io.StringIO()) as stderr:
                code = cli.main(["apps"])
        self.assertEqual(code, 2)
        self.assertIn("non-empty", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
