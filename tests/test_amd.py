from __future__ import annotations

import unittest

from skip_htpc.amd import gpu_status, is_rx580_line, vainfo_has_hevc_main10


ELLESMERE = (
    "01:00.0 VGA compatible controller [0300]: Advanced Micro Devices, Inc. "
    "[AMD/ATI] Ellesmere [Radeon RX 470/480/570/570X/580/580X/590] "
    "[1002:67df] (rev e7)"
)
INTEL = (
    "00:02.0 VGA compatible controller [0300]: Intel Corporation "
    "Xeon E3-1200 v2/3rd Gen Core processor Graphics Controller [8086:0162]"
)
PASCAL = (
    "01:00.0 VGA compatible controller [0300]: NVIDIA Corporation "
    "GP107 [GeForce GTX 1050 Ti] [10de:1c82] (rev a1)"
)
VAINFO = """
VAProfileHEVCMain               : VAEntrypointVLD
VAProfileHEVCMain10             : VAEntrypointVLD
VAProfileVP9Profile0            : VAEntrypointVLD
"""
VAINFO_NO_10 = """
VAProfileHEVCMain               : VAEntrypointVLD
VAProfileVP9Profile0            : VAEntrypointVLD
"""


class AmdTests(unittest.TestCase):
    def test_ellesmere_name_and_device_id(self) -> None:
        self.assertTrue(is_rx580_line(ELLESMERE))
        self.assertTrue(is_rx580_line("VGA ... Radeon RX 580"))
        self.assertTrue(is_rx580_line("Display controller [1002:6FDF]"))
        self.assertFalse(is_rx580_line(INTEL))
        self.assertFalse(is_rx580_line(PASCAL))

    def test_hevc_main10_must_be_a_decode_entry(self) -> None:
        self.assertTrue(vainfo_has_hevc_main10(VAINFO))
        self.assertFalse(vainfo_has_hevc_main10(VAINFO_NO_10))
        self.assertFalse(
            vainfo_has_hevc_main10("VAProfileHEVCMain10 : VAEntrypointEncSlice\n")
        )

    def test_ready_stack(self) -> None:
        text = INTEL + "\n" + ELLESMERE + "\n"
        self.assertEqual(gpu_status(text, "amdgpu", VAINFO), 0)

    def test_other_gpu_empty_and_unconfirmed(self) -> None:
        self.assertEqual(gpu_status(PASCAL, "nvidia", VAINFO), 10)
        self.assertEqual(gpu_status("", "", ""), 13)
        self.assertEqual(gpu_status(ELLESMERE, "", ""), 14)
        self.assertEqual(gpu_status(ELLESMERE, "amdgpu", ""), 14)

    def test_wrong_driver_and_missing_profile(self) -> None:
        self.assertEqual(gpu_status(ELLESMERE, "radeon", VAINFO), 11)
        self.assertEqual(gpu_status(ELLESMERE, "amdgpu", VAINFO_NO_10), 12)


if __name__ == "__main__":
    unittest.main()
