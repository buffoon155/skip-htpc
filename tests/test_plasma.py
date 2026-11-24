from __future__ import annotations

import unittest

from skip_htpc.plasma import (
    ensure_group_keys,
    ensure_kwin,
    ensure_login_session,
    ensure_shortcut,
)


class PlasmaTests(unittest.TestCase):
    def test_shortcut_is_inserted_once_and_replaces_a_different_key(self) -> None:
        original = "[kwin]\nSomething=1\n"
        once = ensure_shortcut(original)
        twice = ensure_shortcut(once)
        self.assertEqual(once, twice)
        self.assertIn("[kwin]\nSomething=1\n", once)
        self.assertEqual(once.count("_launch="), 1)
        self.assertIn("_launch=F13,none,Skip HTPC next", once)

        rebound = ensure_shortcut(once.replace("F13,none,Skip HTPC next", "Alt+X,none,Old"))
        self.assertEqual(rebound.count("_launch="), 1)
        self.assertIn("_launch=F13,none,Skip HTPC next", rebound)
        self.assertNotIn("Alt+X", rebound)

    def test_group_keys_keep_neighbours_and_comments(self) -> None:
        text = "[Compositing]\n# leave this\nEnabled=true\nLatency=1\n\n[Windows]\nPlacement=Smart\n"
        updated = ensure_kwin(text)
        again = ensure_kwin(updated)
        self.assertEqual(updated, again)
        self.assertIn("# leave this\n", updated)
        self.assertIn("Enabled=true\n", updated)
        self.assertIn("AllowApplicationsToBlockCompositing=true\n", updated)
        self.assertIn("UnredirectFullscreen=true\n", updated)
        self.assertIn("Placement=Smart\n", updated)
        self.assertIn("FocusStealingPrevention=0\n", updated)
        self.assertEqual(updated.count("[Compositing]"), 1)
        self.assertEqual(updated.count("[Windows]"), 1)

    def test_login_session_sets_both_keys(self) -> None:
        updated = ensure_login_session("[User]\nIcon=/opt/icon\nSession=plasma\n")
        self.assertIn("Icon=/opt/icon\n", updated)
        self.assertIn("\nSession=plasmax11\n", updated)
        self.assertIn("\nXSession=plasmax11\n", updated)
        self.assertNotIn("Session=plasma\n", updated)

    def test_group_header_must_be_bracketed(self) -> None:
        with self.assertRaises(ValueError):
            ensure_group_keys("", "Compositing", {"Enabled": "true"})


if __name__ == "__main__":
    unittest.main()
