from __future__ import annotations

import unittest

from skip_htpc.config import default_config
from skip_htpc.launch import cycle_target, plan_launch
from skip_htpc.windows import parse_wmctrl_lx


WINDOWS = parse_wmctrl_lx(
    "0x01000001  0 kodi.Kodi  box Kodi\n"
    "0x01000002  0 skip-htpc-netflix.skip-htpc-netflix  box Netflix\n"
)


class LaunchTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = default_config()
        self.order = ["kodi", "youtube", "areena", "netflix"]

    def test_cycle_follows_the_focused_app(self) -> None:
        self.assertEqual(cycle_target("kodi", "netflix", self.order), "youtube")
        self.assertEqual(cycle_target("youtube", "kodi", self.order), "areena")
        self.assertEqual(cycle_target("areena", "youtube", self.order), "netflix")
        self.assertEqual(cycle_target("netflix", "areena", self.order), "kodi")

    def test_cycle_uses_the_last_app_when_focus_is_elsewhere(self) -> None:
        self.assertEqual(cycle_target(None, "youtube", self.order), "areena")
        self.assertEqual(cycle_target("terminal", "netflix", self.order), "kodi")

    def test_cycle_starts_at_kodi(self) -> None:
        self.assertEqual(cycle_target(None, None, self.order), "kodi")

    def test_plan_focuses_a_window_that_is_already_open(self) -> None:
        plan = plan_launch("netflix", WINDOWS, self.config)
        self.assertEqual(plan.action, "focus")
        self.assertEqual(plan.window_id, "0x01000002")

    def test_plan_spawns_when_the_app_is_closed(self) -> None:
        plan = plan_launch("areena", WINDOWS, self.config)
        self.assertEqual(plan.action, "spawn")
        self.assertIsNone(plan.window_id)


if __name__ == "__main__":
    unittest.main()
