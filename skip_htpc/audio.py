from __future__ import annotations


def parse_sinks(text: str) -> list[str]:
    names: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.lower().startswith("sink"):
            continue
        parts = line.split("\t") if "\t" in line else line.split()
        if len(parts) >= 2 and not parts[1].startswith("-"):
            names.append(parts[1])
    return names


def pick_hdmi_sink(text: str, configured: str = "") -> str | None:
    wanted = configured.strip()
    names = parse_sinks(text)
    if wanted:
        return wanted if wanted in names else None
    hdmi = [name for name in names if "hdmi" in name.lower()]
    if not hdmi:
        return None
    # The i7-3770's own HDMI is PCI bus 00. The RX 580 in the x16 slot is
    # bus 01 on this board, and that is the sink the TV is plugged into.
    hdmi.sort(key=lambda name: (0 if "0000_01_" in name.lower() else 1, name.lower()))
    return hdmi[0]
