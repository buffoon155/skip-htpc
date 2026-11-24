from __future__ import annotations

import unittest

from skip_htpc.nvidia import nvidia_status, version_is_branch


REAL_DEPENDS = """
nvidia-driver-580
  Depends: libcuda1-580
  Depends: nvidia-dkms-580
  Depends: nvidia-kernel-common-580
  Depends: xserver-xorg-video-nvidia-580
"""

WRAPPER_DEPENDS = """
nvidia-driver-580
  Depends: nvidia-driver-590
"""

OPEN_DEPENDS = """
nvidia-driver-580
  Depends: nvidia-open
"""


class NvidiaTests(unittest.TestCase):
    def test_real_580_on_current_kernels(self) -> None:
        for kernel in ("6.8.0-79-generic", "6.14.0-1-generic", "7.0.0-1"):
            self.assertEqual(
                nvidia_status("580.196.11-0ubuntu0.24.04.1", REAL_DEPENDS, kernel),
                0,
                kernel,
            )

    def test_epoch_is_ignored(self) -> None:
        self.assertTrue(version_is_branch("1:580.196.11-1"))
        self.assertEqual(nvidia_status("1:580.196.11-1", REAL_DEPENDS, "6.8.0-40-generic"), 0)

    def test_wrapper_is_rejected(self) -> None:
        self.assertEqual(
            nvidia_status("580.196.11-0ubuntu0.24.04.2", WRAPPER_DEPENDS, "6.14.0-1-generic"),
            10,
        )

    def test_open_modules_are_rejected(self) -> None:
        self.assertEqual(
            nvidia_status("580.196.11-0ubuntu1", OPEN_DEPENDS, "6.14.0-1-generic"),
            10,
        )

    def test_other_branches_and_missing_candidate(self) -> None:
        self.assertEqual(nvidia_status("590.44.01-0ubuntu1", "", "6.14.0-1-generic"), 12)
        self.assertEqual(nvidia_status("470.256.02-0ubuntu1", REAL_DEPENDS, "6.8.0-79-generic"), 12)
        self.assertEqual(nvidia_status("(none)", "", "6.8.0-79-generic"), 13)
        self.assertEqual(nvidia_status("", "", "6.8.0-79-generic"), 13)

    def test_unreadable_kernel_is_not_a_reason_to_refuse(self) -> None:
        self.assertEqual(
            nvidia_status("580.196.11-0ubuntu1", REAL_DEPENDS, "not-a-kernel"),
            0,
        )


if __name__ == "__main__":
    unittest.main()
