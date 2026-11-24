from __future__ import annotations

import re

# The GTX 1050 Ti is Pascal (GP107). The Linux 580 branch is the last
# series that drives Maxwell, Pascal, and Volta. A newer branch does not
# bind to this card, and the open kernel modules do not support it.
# A package named 580 that depends on another branch is a transitional
# wrapper and will not bring the desktop up.
DRIVER_BRANCH = 580

_BRANCH = re.compile(
    r"nvidia-(?:driver|dkms|kernel-common)-(\d+)"
)
_OPEN_MODULES = re.compile(r"nvidia-open")


def version_is_branch(version: str, branch: int = DRIVER_BRANCH) -> bool:
    text = version.strip()
    if not text or text == "(none)":
        return False
    if ":" in text:
        text = text.split(":", 1)[1]
    return text.startswith(f"{branch}.")


def depends_on_other_driver(depends: str, branch: int = DRIVER_BRANCH) -> bool:
    if _OPEN_MODULES.search(depends):
        return True
    for match in _BRANCH.finditer(depends):
        if int(match.group(1)) != branch:
            return True
    return False


def nvidia_status(version: str, depends: str, kernel: str) -> int:
    """Exit status for the installer.

    0 install the candidate, 10 candidate pulls another branch or the
    open kernel modules, 12 candidate is not 580.x, 13 there is no
    candidate. kernel is accepted so the installer can pass the running
    release; the 580 branch is updated for current kernels, so the
    release is not a reason to refuse.
    """
    del kernel
    text = version.strip()
    if not text or text == "(none)":
        return 13
    if not version_is_branch(text):
        return 12
    if depends_on_other_driver(depends):
        return 10
    return 0


def nvidia_status_message(code: int) -> str:
    messages = {
        0: "NVIDIA 580 candidate looks usable for the GTX 1050 Ti",
        10: "candidate depends on another NVIDIA branch or the open kernel modules, which do not drive a GTX 1050 Ti",
        12: "candidate is not the 580.x driver",
        13: "apt has no nvidia-driver-580 candidate",
    }
    return messages.get(code, f"unknown NVIDIA check status {code}")
