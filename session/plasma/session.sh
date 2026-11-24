#!/bin/sh
# Plasma (X11) startup for the living-room display.
# The Flirc remote is a keyboard. F13 is a Plasma shortcut.

export LIBVA_DRIVER_NAME="${LIBVA_DRIVER_NAME:-radeonsi}"

if [ -n "${DISPLAY:-}" ] && command -v xset >/dev/null 2>&1; then
  xset s off || true
  xset s noblank || true
  xset -dpms || true
fi

# HDMI on the Radeon RX 580 when PipeWire exposes it.
/usr/local/bin/skip-htpc audio || true

# The library is the screen that comes up. YouTube, Areena, and Netflix
# stay closed until the remote asks for them.
/usr/local/bin/launch.sh kodi || true
