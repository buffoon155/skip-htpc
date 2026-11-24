from __future__ import annotations

import unittest

from skip_htpc.audio import parse_sinks, pick_hdmi_sink


SINKS = (
    "0\talsa_output.pci-0000_00_1b.0.analog-stereo\tmodule-alsa-card.c\tSUSPENDED\n"
    "1\talsa_output.pci-0000_01_00.1.hdmi-stereo\tmodule-alsa-card.c\tRUNNING\n"
)


class AudioTests(unittest.TestCase):
    def test_parse_and_pick_hdmi(self) -> None:
        self.assertEqual(
            parse_sinks(SINKS),
            [
                "alsa_output.pci-0000_00_1b.0.analog-stereo",
                "alsa_output.pci-0000_01_00.1.hdmi-stereo",
            ],
        )
        self.assertEqual(
            pick_hdmi_sink(SINKS),
            "alsa_output.pci-0000_01_00.1.hdmi-stereo",
        )

    def test_configured_sink_must_exist(self) -> None:
        self.assertEqual(
            pick_hdmi_sink(SINKS, "alsa_output.pci-0000_01_00.1.hdmi-stereo"),
            "alsa_output.pci-0000_01_00.1.hdmi-stereo",
        )
        self.assertIsNone(pick_hdmi_sink(SINKS, "missing"))

    def test_no_hdmi_leaves_the_default(self) -> None:
        self.assertIsNone(pick_hdmi_sink("0\talsc_output.analog\tmodule\tIDLE\n"))


if __name__ == "__main__":
    unittest.main()
