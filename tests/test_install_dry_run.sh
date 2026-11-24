#!/bin/bash
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
out=$("$root/install/install.sh" --dry-run)
printf '%s\n' "$out" | grep -q 'skip-htpc install: dry-run'
printf '%s\n' "$out" | grep -q 'packages:.*openbox'
printf '%s\n' "$out" | grep -q 'browser: google-chrome-stable'
printf '%s\n' "$out" | grep -q 'nvidia: not requested'
printf '%s\n' "$out" | grep -q 'F13 -> /usr/local/bin/launch.sh next'

nvidia=$("$root/install/install.sh" --dry-run --nvidia --no-chrome)
printf '%s\n' "$nvidia" | grep -q 'nvidia: requested'
printf '%s\n' "$nvidia" | grep -q 'browser: skipped'

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
