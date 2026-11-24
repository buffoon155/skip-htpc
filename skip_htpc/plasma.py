from __future__ import annotations

# Plasma 6 registers a command shortcut from a desktop file in
# ~/.local/share/applications plus a group in kglobalshortcutsrc.
# The group name is the desktop file's basename.
SHORTCUT_GROUP = "[services][skip-htpc-next.desktop]"
SHORTCUT_KEYS = {"_launch": "F13,none,Skip HTPC next"}

LOGIN_SESSION = "plasmax11"


def ensure_group_keys(text: str, group: str, keys: dict[str, str]) -> str:
    """Insert or replace keys in one INI group, leaving every other group."""
    header = group.strip()
    if not (header.startswith("[") and header.endswith("]")):
        raise ValueError(f"group must be [Name], not {group!r}")
    lines = text.splitlines()
    start = next((index for index, line in enumerate(lines) if line.strip() == header), None)
    if start is None:
        block = [header, *[f"{key}={value}" for key, value in keys.items()]]
        if lines and lines[-1] != "":
            lines.append("")
        lines.extend(block)
        return "\n".join(lines).rstrip() + "\n"

    end = len(lines)
    for index in range(start + 1, len(lines)):
        stripped = lines[index].strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            end = index
            break

    body: list[str] = []
    seen: set[str] = set()
    for line in lines[start + 1 : end]:
        stripped = line.strip()
        if not stripped or stripped.startswith(("#", ";")):
            body.append(line)
            continue
        name = line.split("=", 1)[0].strip()
        if name in keys:
            if name not in seen:
                body.append(f"{name}={keys[name]}")
                seen.add(name)
            continue
        body.append(line)
    for key, value in keys.items():
        if key not in seen:
            body.append(f"{key}={value}")
    updated = lines[: start + 1] + body + lines[end:]
    return "\n".join(updated).rstrip() + "\n"


def ensure_shortcut(text: str) -> str:
    return ensure_group_keys(text, SHORTCUT_GROUP, SHORTCUT_KEYS)


def ensure_kwin(text: str) -> str:
    """Let Kodi and Chrome take the TV on the X11 session."""
    text = ensure_group_keys(
        text,
        "[Compositing]",
        {
            "AllowApplicationsToBlockCompositing": "true",
            "UnredirectFullscreen": "true",
        },
    )
    return ensure_group_keys(
        text,
        "[Windows]",
        {"FocusStealingPrevention": "0"},
    )


def ensure_login_session(text: str, session: str = LOGIN_SESSION) -> str:
    return ensure_group_keys(
        text,
        "[User]",
        {"Session": session, "XSession": session},
    )
