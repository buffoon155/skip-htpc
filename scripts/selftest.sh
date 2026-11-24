#!/bin/bash
# Checks the launcher contract: commands, Chrome app URLs, same-line
# cycle_order, and the extension's keydown / spatial / orange outline.
set -euo pipefail

root=$(cd "$(dirname "$0")/.." && pwd)
cd "$root"

fail() {
  echo "selftest: $*" >&2
  exit 1
}

bash -n launch.sh
bash -n scripts/selftest.sh

if grep -n 'getline' launch.sh; then
  fail "cycle_order must be parsed from the same-line list"
fi

grep -qx 'cycle_order: \[kodi, netflix, areena\]' config.yaml
grep -qx 'netflix_url: https://www.netflix.com' config.yaml
grep -qx 'areena_url: https://areena.yle.fi' config.yaml
grep -q -- '--app=${netflix_url}' launch.sh
grep -q -- '--app=${areena_url}' launch.sh
grep -q 'google-chrome-stable' launch.sh
grep -q 'NETFLIX_URL_DEFAULT=https://www.netflix.com' launch.sh
grep -q 'AREENA_URL_DEFAULT=https://areena.yle.fi' launch.sh

grep -q 'addEventListener("keydown"' extension/content.js
grep -q ', true);' extension/content.js
grep -q '#ff6a00' extension/content.js
grep -q 'outline' extension/content.js
grep -q "data-uia='title-card'" extension/content.js
grep -q handleNext extension/content.js
grep -q Takaisin extension/content.js
grep -q 'Exec=/usr/local/bin/launch.sh kodi' session/autostart/skip-htpc.desktop
grep -q 'ExecStart=/usr/local/bin/launch.sh kodi' session/systemd/skip-htpc.service
grep -q 'function navigate' extension/spatial.js

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

status=$(SKIP_HTPC_STATE="$tmp/state" SKIP_HTPC_BROWSER=google-chrome ./launch.sh status)
printf '%s\n' "$status" | grep -qx 'cycle_order: kodi netflix areena'
printf '%s\n' "$status" | grep -qx 'netflix: https://www.netflix.com'
printf '%s\n' "$status" | grep -qx 'areena: https://areena.yle.fi'
printf '%s\n' "$status" | grep -qx 'browser: google-chrome'

dry_netflix=$(SKIP_HTPC_STATE="$tmp/state" SKIP_HTPC_DRY=1 SKIP_HTPC_BROWSER=google-chrome ./launch.sh netflix)
printf '%s\n' "$dry_netflix" | grep -qx 'google-chrome --app=https://www.netflix.com'

dry_areena=$(SKIP_HTPC_STATE="$tmp/state" SKIP_HTPC_DRY=1 SKIP_HTPC_BROWSER=chromium ./launch.sh areena)
printf '%s\n' "$dry_areena" | grep -qx 'chromium --app=https://areena.yle.fi'

first=$(SKIP_HTPC_STATE="$tmp/state" SKIP_HTPC_DRY=1 SKIP_HTPC_DEBOUNCE=0 ./launch.sh next)
printf '%s\n' "$first" | grep -qx 'next: kodi'
printf '%s\n' "$first" | grep -qx 'kodi'

second=$(SKIP_HTPC_STATE="$tmp/state" SKIP_HTPC_DRY=1 SKIP_HTPC_DEBOUNCE=0 ./launch.sh next)
printf '%s\n' "$second" | grep -qx 'next: netflix'
printf '%s\n' "$second" | grep -qx 'google-chrome --app=https://www.netflix.com' \
  || printf '%s\n' "$second" | grep -q -- '--app=https://www.netflix.com'

printf 'cycle_order:\n  - kodi\n  - netflix\n' > "$tmp/bad.yaml"
if SKIP_HTPC_CONFIG_YAML="$tmp/bad.yaml" ./launch.sh status >/dev/null 2>"$tmp/bad.err"; then
  fail "a multiline cycle_order was accepted"
fi
grep -q 'same-line' "$tmp/bad.err"

if [[ -x "$(command -v node)" ]]; then
  node --test extension/spatial.test.mjs >/dev/null
fi

echo "selftest: ok"
