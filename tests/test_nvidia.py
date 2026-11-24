from __future__ import annotations

import unittest

from skip_htpc.nvidia import nvidia_status, version_is_470


REAL_DEPENDS = """
nvidia-driver-470
  Depends: libcuda1-470
  Depends: nvidia-dkms-470
  Depends: nvidia-kernel-common-470
  Depends: xserver-xorg-video-nvidia-470
"""

WRAPPER_DEPENDS = """
nvidia-driver-470
  Depends: nvidia-driver-535
"""


class NvidiaTests(unittest.TestCase):
    def test_real_470_on_jammy_kernels(self) -> None:
        for kernel in ("5.15.0-122-generic", "6.8.0-79-generic", "6.13.0-1-generic"):
            self.assertEqual(
                nvidia_status("470.256.02-0ubuntu0.22.04.1", REAL_DEPENDS, kernel),
                0,
                kernel,
            )

    def test_epoch_is_ignored(self) -> None:
        self.assertTrue(version_is_470("1:470.256.02-1"))
        self.assertEqual(nvidia_status("1:470.256.02-1", REAL_DEPENDS, "6.8.0-40-generic"), 0)

    def test_wrapper_is_rejected(self) -> None:
        self.assertEqual(
            nvidia_status("470.256.02-0ubuntu0.22.04.2", WRAPPER_DEPENDS, "6.8.0-79-generic"),
            10,
        )

    def test_newer_branch_and_missing_candidate(self) -> None:
        self.assertEqual(nvidia_status("535.183.01-0ubuntu1", "", "6.8.0-79-generic"), 12)
        self.assertEqual(nvidia_status("(none)", "", "6.8.0-79-generic"), 13)
        self.assertEqual(nvidia_status("", "", "6.8.0-79-generic"), 13)

    def test_new_kernels_are_rejected(self) -> None:
        self.assertEqual(
            nvidia_status("470.256.02-0ubuntu1", REAL_DEPENDS, "6.14.0-1-generic"),
            11,
        )
        self.assertEqual(nvidia_status("470.256.02-0ubuntu1", REAL_DEPENDS, "7.0.0-1"), 11)
        self.assertEqual(nvidia_status("470.256.02-0ubuntu1", REAL_DEPENDS, "not-a-kernel"), 11)


if __name__ == "__main__":
    unittest.main()
