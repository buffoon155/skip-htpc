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
        self.assertEqual(stdout.getvalue().strip(), "kodi youtube areena netflix")

    def test_launch_needs_an_app(self) -> None:
        with redirect_stderr(io.StringIO()):
            self.assertEqual(cli.main(["launch"]), 2)
        with redirect_stderr(io.StringIO()) as stderr:
            self.assertEqual(cli.main(["launch", "lounge"]), 2)
        self.assertIn("unknown app", stderr.getvalue())

    def test_gpu_ok_command(self) -> None:
        ellesmere = (
            "01:00.0 VGA compatible controller: Advanced Micro Devices, Inc. "
            "Ellesmere [1002:67df]"
        )
        vainfo = "VAProfileHEVCMain10 : VAEntrypointVLD"
        with redirect_stderr(io.StringIO()):
            self.assertEqual(
                cli.main(
                    [
                        "gpu-ok",
                        "--lspci",
                        ellesmere,
                        "--driver",
                        "amdgpu",
                        "--vainfo",
                        vainfo,
                    ]
                ),
                0,
            )
            self.assertEqual(
                cli.main(
                    [
                        "gpu-ok",
                        "--lspci",
                        "01:00.0 VGA compatible controller: NVIDIA Corporation GP107",
                        "--driver",
                        "nvidia",
                        "--vainfo",
                        vainfo,
                    ]
                ),
                10,
            )

    def test_patch_plasma_writes_f13(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "kglobalshortcutsrc"
            path.write_text("[kwin]\nA=1\n", encoding="utf-8")
            with redirect_stdout(io.StringIO()):
                self.assertEqual(cli.main(["patch-plasma", str(path)]), 0)
            text = path.read_text(encoding="utf-8")
            self.assertIn("[kwin]\nA=1\n", text)
            self.assertIn("_launch=F13,none,Skip HTPC next", text)

    def test_extension_manifest(self) -> None:
        root = Path(__file__).resolve().parents[1]
        ok, detail = cli.extension_manifest_ok(root / "extension" / "manifest.json")
        self.assertTrue(ok, detail)
        self.assertIn("spatial", detail.lower())

    def test_doctor_reports_a_missing_browser(self) -> None:
        with mock.patch.object(cli, "load_config", default_config):
            with mock.patch.object(cli, "resolve_browser", return_value=None):
                with mock.patch.object(cli, "shutil_which", return_value=None):
                    with mock.patch.object(cli, "_gpu_report", return_value="gpu: unseen"):
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
