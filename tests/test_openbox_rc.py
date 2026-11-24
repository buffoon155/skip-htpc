from __future__ import annotations

import unittest

from skip_htpc.openbox_rc import ensure_cycle_keybind

RC = """<?xml version="1.0" encoding="UTF-8"?>
<openbox_config xmlns="http://openbox.org/3.4/rc">
  <keyboard>
    <keybind key="A-F4">
      <action name="Close"/>
    </keybind>
  </keyboard>
  <applications>
  </applications>
</openbox_config>
"""


class OpenboxRcTests(unittest.TestCase):
    def test_inserts_f13_and_app_rules_once(self) -> None:
        once = ensure_cycle_keybind(RC)
        twice = ensure_cycle_keybind(once)
        self.assertEqual(once, twice)
        self.assertEqual(once.count('key="F13"'), 1)
        self.assertIn("/usr/local/bin/skip-htpc cycle", once)
        self.assertIn('class="skip-htpc-netflix"', once)
        self.assertIn('class="skip-htpc-areena"', once)
        self.assertIn('key="A-F4"', once)

    def test_missing_keyboard_section_is_an_error(self) -> None:
        with self.assertRaises(ValueError):
            ensure_cycle_keybind("<openbox_config></openbox_config>\n")


if __name__ == "__main__":
    unittest.main()
