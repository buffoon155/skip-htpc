from __future__ import annotations

import re

# Kepler (GTX 660 / GK106) support ended with the 470 branch. A package
# named 470 that depends on 495 or newer is the Ubuntu transitional wrapper
# and will not bring the desktop up on this GPU.
_NEWER_DRIVER = re.compile(
    r"nvidia-(?:driver|dkms|kernel-common)-(\d+)"
)


def kernel_tuple(release: str) -> tuple[int, int] | None:
    base = release.split("-", 1)[0]
    parts = base.split(".")
    if not parts or not parts[0]:
        return None
    try:
        major = int(parts[0])
        minor = int(parts[1]) if len(parts) > 1 else 0
    except ValueError:
        return None
    return major, minor


def kernel_too_new_for_470(release: str) -> bool:
    parsed = kernel_tuple(release)
    if parsed is None:
        return True
    major, minor = parsed
    return major > 6 or (major == 6 and minor >= 14)


def version_is_470(version: str) -> bool:
    text = version.strip()
    if not text or text == "(none)":
        return False
    if ":" in text:
        text = text.split(":", 1)[1]
    return text.startswith("470.")


def depends_on_unsupported_driver(depends: str) -> bool:
    for match in _NEWER_DRIVER.finditer(depends):
        if int(match.group(1)) >= 495:
            return True
    return False


def nvidia_status(version: str, depends: str, kernel: str) -> int:
    """Exit status for the installer.

    0 install the candidate, 10 candidate is a newer-driver wrapper,
    11 kernel is too new or unreadable, 12 candidate is not 470.x,
    13 there is no candidate.
    """
    if kernel_too_new_for_470(kernel):
        return 11
    text = version.strip()
    if not text or text == "(none)":
        return 13
    if not version_is_470(text):
        return 12
    if depends_on_unsupported_driver(depends):
        return 10
    return 0


def nvidia_status_message(code: int) -> str:
    messages = {
        0: "NVIDIA 470 candidate looks usable on this kernel",
        10: "candidate depends on a newer NVIDIA driver that does not support the GTX 660",
        11: "kernel is 6.14 or newer, or its version could not be read; unpatched NVIDIA 470 will not build",
        12: "candidate is not the 470.x driver",
        13: "apt has no nvidia-driver-470 candidate",
    }
    return messages.get(code, f"unknown NVIDIA check status {code}")
