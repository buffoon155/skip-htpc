from __future__ import annotations

import unittest

from skip_htpc.config import default_config
from skip_htpc.windows import (
    app_for_window,
    focused_app,
    parse_wmctrl_lx,
    windows_for_app,
)


SAMPLE = """
0x01200003  0 kodi.Kodi  livingroom Kodi
0x0140000a  0 skip-htpc-netflix.skip-htpc-netflix  livingroom Netflix
0x01600001  0 skip-htpc-areena.Skip-htpc-areena  livingroom Yle Areena
0x01800002  0 gnome-terminal.Gnome-terminal  livingroom Terminal
not a window line
"""


class WindowTests(unittest.TestCase):
    def test_parse_and_match(self) -> None:
        config = default_config()
        windows = parse_wmctrl_lx(SAMPLE)
        self.assertEqual(len(windows), 4)
        self.assertEqual(app_for_window(windows[0], config), "kodi")
        self.assertEqual(app_for_window(windows[1], config), "netflix")
        self.assertEqual(app_for_window(windows[2], config), "areena")
        self.assertIsNone(app_for_window(windows[3], config))
        self.assertEqual(windows[2].title, "Yle Areena")
        self.assertEqual(windows_for_app(windows, config, "kodi")[0].id_hex, "0x01200003")

    def test_focused_app_compares_decimal_ids(self) -> None:
        config = default_config()
        windows = parse_wmctrl_lx(SAMPLE)
        netflix_id = int("0x0140000a", 16)
        self.assertEqual(focused_app(windows, netflix_id, config), "netflix")
        self.assertIsNone(focused_app(windows, 1, config))
        self.assertIsNone(focused_app(windows, None, config))


if __name__ == "__main__":
    unittest.main()
