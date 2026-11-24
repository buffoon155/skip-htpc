#!/bin/bash
# Install the Skip HTPC session on the spare AMD64 PC (GeForce GTX 660).
# Default is a dry run. Apply with: sudo ./install/install.sh --yes
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
HTPC_USER=${HTPC_USER:-htpc}
DRY=1
NVIDIA=0
CHROME=1
PACKAGES=(
  openbox
  lightdm
  xorg
  kodi
  wmctrl
  xdotool
  x11-xserver-utils
  python3
  ca-certificates
  curl
  gnupg
  dbus-x11
  pciutils
)

usage() {
  cat <<EOF
usage: install.sh [--dry-run] [--yes] [--nvidia] [--no-chrome]

  --dry-run    print the plan (this is the default)
  --yes        install as root on the HTPC
  --nvidia     also install the NVIDIA 470 driver when the candidate is really 470.x
  --no-chrome  do not add Google's apt repo or install google-chrome-stable

HTPC_USER overrides the autologin account (default: htpc).
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY=1 ;;
    --yes) DRY=0 ;;
    --nvidia) NVIDIA=1 ;;
    --no-chrome) CHROME=0 ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
  shift
done

if [[ ! "$HTPC_USER" =~ ^[a-z_][a-z0-9_-]*$ ]]; then
  echo "HTPC_USER must be a simple account name" >&2
  exit 2
fi

if id "$HTPC_USER" >/dev/null 2>&1; then
  HOME_DIR=$(getent passwd "$HTPC_USER" | cut -d: -f6)
else
  HOME_DIR="/home/$HTPC_USER"
fi

if [[ "$DRY" -eq 1 ]]; then
  echo "skip-htpc install: dry-run"
  echo "pass --yes as root on the HTPC to apply"
else
  if [[ "$(id -u)" -ne 0 ]]; then
    echo "install.sh --yes must run as root" >&2
    exit 1
  fi
  arch=$(dpkg --print-architecture)
  if [[ "$arch" != amd64 ]]; then
    echo "this installer is for the AMD64 HTPC, not $arch" >&2
    exit 1
  fi
  echo "skip-htpc install: applying on the spare HTPC"
  echo "lightdm will autologin ${HTPC_USER} to Openbox and replace another display manager"
fi

if [[ -r /etc/os-release ]]; then
  # shellcheck disable=SC1091
  . /etc/os-release
  echo "os: ${PRETTY_NAME:-unknown} (installer targets Ubuntu 22.04)"
else
  echo "os: unknown (installer targets Ubuntu 22.04)"
fi
echo "user: ${HTPC_USER}"
echo "home: ${HOME_DIR}"
echo "packages: ${PACKAGES[*]}"
if [[ "$CHROME" -eq 1 ]]; then
  echo "browser: google-chrome-stable"
else
  echo "browser: skipped"
fi
if [[ "$NVIDIA" -eq 1 ]]; then
  echo "nvidia: requested"
else
  echo "nvidia: not requested"
fi
echo "session: lightdm autologin, openbox, F13 -> /usr/local/bin/launch.sh next"

if [[ "$DRY" -eq 1 ]]; then
  exit 0
fi

export DEBIAN_FRONTEND=noninteractive
export PYTHONPATH="${ROOT}${PYTHONPATH:+:$PYTHONPATH}"

echo "lightdm shared/default-x-display-manager select lightdm" | debconf-set-selections
apt-get update
apt-get install -y "${PACKAGES[@]}"

if [[ "$CHROME" -eq 1 ]]; then
  if [[ ! -f /etc/apt/sources.list.d/google-chrome.list ]]; then
    install -d /usr/share/keyrings
    tmpkey=$(mktemp)
    curl -fsSL https://dl.google.com/linux/linux_signing_key.pub -o "$tmpkey"
    rm -f /usr/share/keyrings/google-chrome.gpg
    gpg --batch --yes --dearmor -o /usr/share/keyrings/google-chrome.gpg "$tmpkey"
    rm -f "$tmpkey"
    chmod 0644 /usr/share/keyrings/google-chrome.gpg
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] https://dl.google.com/linux/chrome/deb/ stable main" \
      > /etc/apt/sources.list.d/google-chrome.list
    apt-get update
  fi
  if ! command -v google-chrome-stable >/dev/null 2>&1; then
    apt-get install -y google-chrome-stable
  fi
fi

if ! id "$HTPC_USER" >/dev/null 2>&1; then
  adduser --disabled-password --gecos "Skip HTPC" "$HTPC_USER"
  HOME_DIR=$(getent passwd "$HTPC_USER" | cut -d: -f6)
fi

groups=()
for group in audio video render input; do
  if getent group "$group" >/dev/null; then
    groups+=("$group")
  fi
done
if [[ ${#groups[@]} -gt 0 ]]; then
  joined=$(IFS=,; echo "${groups[*]}")
  usermod -aG "$joined" "$HTPC_USER"
fi

DEST=/usr/local/share/skip-htpc
if [[ "$DEST" != /usr/local/share/skip-htpc ]]; then
  echo "refusing to install outside /usr/local/share/skip-htpc" >&2
  exit 1
fi
mkdir -p "$DEST"
for part in skip_htpc extension session kodi docs; do
  rm -rf "${DEST}/${part}"
  cp -a "${ROOT}/${part}" "${DEST}/${part}"
done
cp -a "${ROOT}/README.md" "${DEST}/README.md"
cp -a "${ROOT}/config.yaml" "${DEST}/config.yaml"
install -m 0755 "${ROOT}/install/skip-htpc" /usr/local/bin/skip-htpc
install -m 0755 "${ROOT}/launch.sh" /usr/local/bin/launch.sh
install -d /etc/skip-htpc
if [[ ! -f /etc/skip-htpc/config.yaml ]]; then
  install -m 0644 "${ROOT}/config.yaml" /etc/skip-htpc/config.yaml
fi

install -d /etc/lightdm/lightdm.conf.d
sed "s/@HTPC_USER@/${HTPC_USER}/g" \
  "${ROOT}/install/lightdm/skip-htpc.conf.in" \
  > /etc/lightdm/lightdm.conf.d/skip-htpc.conf
chmod 0644 /etc/lightdm/lightdm.conf.d/skip-htpc.conf
printf '%s\n' /usr/sbin/lightdm > /etc/X11/default-display-manager
systemctl enable lightdm
systemctl disable gdm gdm3 >/dev/null 2>&1 || true

install -d "${HOME_DIR}/.config/openbox" "${HOME_DIR}/.kodi/userdata/keymaps"
install -m 0755 "${ROOT}/session/openbox/autostart" "${HOME_DIR}/.config/openbox/autostart"
install -m 0644 "${ROOT}/session/openbox/menu.xml" "${HOME_DIR}/.config/openbox/menu.xml"
if [[ ! -f "${HOME_DIR}/.config/openbox/rc.xml" ]]; then
  if [[ ! -f /etc/xdg/openbox/rc.xml ]]; then
    echo "openbox rc.xml is missing after the package install" >&2
    exit 1
  fi
  cp /etc/xdg/openbox/rc.xml "${HOME_DIR}/.config/openbox/rc.xml"
fi
python3 -m skip_htpc patch-openbox "${HOME_DIR}/.config/openbox/rc.xml"
install -m 0644 \
  "${ROOT}/kodi/userdata/keymaps/skip-htpc.xml" \
  "${HOME_DIR}/.kodi/userdata/keymaps/skip-htpc.xml"
chown -R "${HTPC_USER}:${HTPC_USER}" \
  "${HOME_DIR}/.config/openbox" \
  "${HOME_DIR}/.kodi"

install_nvidia() {
  local ver dep code
  ver=$(apt-cache policy nvidia-driver-470 | awk '/Candidate:/ {print $2; exit}')
  dep=$(apt-cache depends nvidia-driver-470 2>/dev/null || true)
  set +e
  python3 -m skip_htpc nvidia-ok --version "${ver:-}" --depends "$dep" --kernel "$(uname -r)"
  code=$?
  set -e
  if [[ "$code" -eq 10 ]]; then
    codename=${VERSION_CODENAME:-}
    if [[ -z "$codename" && -r /etc/os-release ]]; then
      # shellcheck disable=SC1091
      . /etc/os-release
      codename=${VERSION_CODENAME:-}
    fi
    if [[ -z "$codename" ]]; then
      echo "cannot pin the 470 wrapper without VERSION_CODENAME" >&2
      return 1
    fi
    echo "nvidia-driver-470 candidate depends on a newer driver; pinning ${codename}-updates away"
    sed "s/@CODENAME@/${codename}/g" "${ROOT}/install/apt/nvidia-470.pref" \
      > /etc/apt/preferences.d/nvidia-470
    chmod 0644 /etc/apt/preferences.d/nvidia-470
    apt-get update
    ver=$(apt-cache policy nvidia-driver-470 | awk '/Candidate:/ {print $2; exit}')
    dep=$(apt-cache depends nvidia-driver-470 2>/dev/null || true)
    set +e
    python3 -m skip_htpc nvidia-ok --version "${ver:-}" --depends "$dep" --kernel "$(uname -r)"
    code=$?
    set -e
  fi
  if [[ "$code" -ne 0 ]]; then
    echo "not installing a NVIDIA driver (status ${code})." >&2
    apt-cache policy nvidia-driver-470 >&2 || true
    echo "The Openbox session is installed. The display stays on its current driver." >&2
    echo "See docs/hardware.md before trying again." >&2
    return 1
  fi
  if command -v mokutil >/dev/null 2>&1; then
    if mokutil --sb-state 2>/dev/null | grep -qi "SecureBoot enabled"; then
      echo "Secure Boot is on. The 470 module is DKMS and needs a MOK enrollment, or Secure Boot turned off, before the reboot will show a picture."
    fi
  fi
  apt-get install -y "linux-headers-$(uname -r)" nvidia-driver-470
}

if [[ "$NVIDIA" -eq 1 ]]; then
  install_nvidia
fi

cat <<EOF

Installed. Reboot, then:

  1. Kodi should be on the TV. Settings → System → Display, expert settings:
     full screen, and "Use full screen window" so Netflix can be raised over it.
  2. Press the spare Flirc key (F13) to cycle Kodi → Netflix → Areena.
  3. Sign in to Netflix and Areena once with a keyboard. The profiles are kept.
  4. Program the Flirc as a keyboard. Leave volume off it if the amp still
     hears those IR codes directly. See docs/remote.md.

Do not run ubuntu-drivers install on this PC. A newer NVIDIA branch does not
support the GTX 660.
EOF
