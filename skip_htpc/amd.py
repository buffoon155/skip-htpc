from __future__ import annotations

import re

# lspci names the 4 GB and 8 GB RX 580 as Ellesmere, in one line that also
# lists the RX 470/480/570/590. 67df is that chip. 6fdf is the Polaris 20
# part sold as an RX 580 as well.
RX580_DEVICES = frozenset({"67df", "6fdf"})

_DEVICE = re.compile(r"1002:([0-9a-fA-F]{4})")
_VGA = re.compile(r"VGA|3D controller|Display controller")


def vga_lines(lspci_text: str) -> list[str]:
    lines: list[str] = []
    for raw in lspci_text.splitlines():
        line = raw.strip()
        if line and _VGA.search(line):
            lines.append(line)
    return lines


def is_rx580_line(line: str) -> bool:
    lowered = line.lower()
    if "rx 580" in lowered or "rx580" in lowered:
        return True
    if "ellesmere" in lowered:
        return True
    for match in _DEVICE.finditer(line):
        if match.group(1).lower() in RX580_DEVICES:
            return True
    return False


def vainfo_has_hevc_main10(vainfo_text: str) -> bool:
    for line in vainfo_text.splitlines():
        if "VAProfileHEVCMain10" in line and "VAEntrypointVLD" in line:
            return True
    return False


def gpu_status(lspci_text: str, driver: str, vainfo_text: str) -> int:
    """Exit status for the installer and for doctor.

    0 the RX 580 is on amdgpu and VA-API lists HEVC Main 10.
    10 a display device is present and none of them is an RX 580.
    11 the RX 580 is bound to a driver other than amdgpu.
    12 amdgpu is up and VA-API has no HEVC Main 10 decode entry.
    13 lspci shows no display device.
    14 the card matches, and the driver or vainfo text was left empty.
    """
    lines = vga_lines(lspci_text)
    if not lines:
        return 13
    if not any(is_rx580_line(line) for line in lines):
        return 10
    bound = driver.strip()
    if bound and bound != "amdgpu":
        return 11
    probed = vainfo_text.strip()
    if probed and not vainfo_has_hevc_main10(probed):
        return 12
    if not bound or not probed:
        return 14
    return 0


def gpu_status_message(code: int) -> str:
    messages = {
        0: "Radeon RX 580 is on amdgpu and VA-API lists HEVC Main 10",
        10: "display GPU is not an Ellesmere Radeon RX 580",
        11: "Radeon RX 580 is not bound to amdgpu",
        12: "VA-API has no HEVC Main 10 decode entry",
        13: "lspci shows no display device",
        14: "Radeon RX 580 is present; the driver or VA-API was not confirmed",
    }
    return messages.get(code, f"unknown GPU check status {code}")
