#!/bin/bash
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
out=$("$root/install/install.sh" --dry-run)
printf '%s\n' "$out" | grep -q 'skip-htpc install: dry-run'
printf '%s\n' "$out" | grep -q 'packages:.*plasma-session-x11'
printf '%s\n' "$out" | grep -q 'packages:.*mesa-libgallium'
printf '%s\n' "$out" | grep -q 'packages:.*kodi'
printf '%s\n' "$out" | grep -q 'browser: google-chrome-stable'
printf '%s\n' "$out" | grep -q 'Radeon RX 580'
printf '%s\n' "$out" | grep -q 'installer targets Kubuntu 26.04'
printf '%s\n' "$out" | grep -q 'F13 -> /usr/local/bin/launch.sh next'
printf '%s\n' "$out" | grep -q 'plasmax11'
printf '%s\n' "$out" | grep -q 'boot: plasma autostart runs the session script'

if grep -q 'nvidia-driver' "$root/install/install.sh"; then
  echo "installer still names a NVIDIA driver package" >&2
  exit 1
fi
if grep -q 'user-session=openbox' "$root/install/install.sh"; then
  echo "installer still selects an Openbox session" >&2
  exit 1
fi

skipped=$("$root/install/install.sh" --dry-run --no-chrome)
printf '%s\n' "$skipped" | grep -q 'browser: skipped'

help=$("$root/install/install.sh" --help)
printf '%s\n' "$help" | grep -q -- '--yes'

set +e
"$root/install/install.sh" --not-a-flag >/dev/null 2>&1
code=$?
set -e
test "$code" -eq 2

if [[ "$(id -u)" -ne 0 ]]; then
  set +e
  "$root/install/install.sh" --yes >/dev/null 2>"$root/tests/.yes-stderr"
  code=$?
  set -e
  test "$code" -eq 1
  grep -q 'must run as root' "$root/tests/.yes-stderr"
  rm -f "$root/tests/.yes-stderr"
fi
