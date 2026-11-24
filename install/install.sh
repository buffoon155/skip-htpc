#!/bin/bash
# Install the Skip HTPC session on Kubuntu 26 with a Radeon RX 580.
# Default is a dry run. Apply with: sudo ./install/install.sh --yes
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
HTPC_USER=${HTPC_USER:-htpc}
DRY=1
CHROME=1
PACKAGES=(
  plasma-session-x11
  sddm
  xorg
  mesa-libgallium
  vainfo
  linux-firmware
  kodi
  wmctrl
  xdotool
  x11-xserver-utils
  pulseaudio-utils
  python3
  ca-certificates
  curl
  gnupg
  dbus-x11
  pciutils
)

usage() {
  cat <<EOF
usage: install.sh [--dry-run] [--yes] [--no-chrome]

  --dry-run    print the plan (this is the default)
  --yes        install as root on the Kubuntu HTPC
  --no-chrome  do not add Google's apt repo or install google-chrome-stable

HTPC_USER overrides the autologin account (default: htpc).
The login session is Plasma (X11), desktop file plasmax11. Kubuntu 26.04
and 26.10 are accepted. The GPU check expects an Ellesmere Radeon RX 580.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY=1 ;;
    --yes) DRY=0 ;;
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
  echo "sddm will autologin ${HTPC_USER} into Plasma (X11)"
fi

if [[ -r /etc/os-release ]]; then
  # shellcheck disable=SC1091
  . /etc/os-release
  echo "os: ${PRETTY_NAME:-unknown} (installer targets Kubuntu 26.04)"
else
  echo "os: unknown (installer targets Kubuntu 26.04)"
fi
echo "user: ${HTPC_USER}"
echo "home: ${HOME_DIR}"
echo "packages: ${PACKAGES[*]}"
if [[ "$CHROME" -eq 1 ]]; then
  echo "browser: google-chrome-stable"
else
  echo "browser: skipped"
fi
echo "gpu: Radeon RX 580 via amdgpu and Mesa VA-API"
echo "session: sddm autologin, plasmax11, F13 -> /usr/local/bin/launch.sh next"
echo "boot: plasma autostart runs the session script, which starts Kodi"

if [[ "$DRY" -eq 1 ]]; then
  exit 0
fi

case "${VERSION_ID:-}" in
  26.04|26.10) ;;
  *)
    echo "this installer applies on Kubuntu 26.04 or 26.10. This machine is ${VERSION_ID:-unknown}." >&2
    exit 1
    ;;
esac

if [[ ! -x /usr/bin/startplasma-wayland && ! -x /usr/bin/startplasma-x11 ]]; then
  echo "Plasma is not installed. Install Kubuntu 26.04, then run this again." >&2
  exit 1
fi

export DEBIAN_FRONTEND=noninteractive
export PYTHONPATH="${ROOT}${PYTHONPATH:+:$PYTHONPATH}"

apt-get update
apt-get install -y "${PACKAGES[@]}"
if apt-cache show mesa-vulkan-drivers >/dev/null 2>&1; then
  apt-get install -y mesa-vulkan-drivers
fi
if apt-cache show xserver-xorg-video-amdgpu >/dev/null 2>&1; then
  apt-get install -y xserver-xorg-video-amdgpu
fi

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

gpu_text=$(lspci -nn 2>/dev/null || true)
set +e
python3 -m skip_htpc gpu-ok --lspci "$gpu_text" --driver "" --vainfo ""
gpu_code=$?
set -e
if [[ "$gpu_code" -eq 10 ]]; then
  echo "Refusing to change the login session: the display GPU is not a Radeon RX 580." >&2
  exit 1
fi
if [[ "$gpu_code" -eq 13 ]]; then
  echo "lspci shows no display device. The session will still be installed."
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
chmod 0755 "${DEST}/session/plasma/session.sh"
cp -a "${ROOT}/README.md" "${DEST}/README.md"
cp -a "${ROOT}/config.yaml" "${DEST}/config.yaml"
install -m 0755 "${ROOT}/install/skip-htpc" /usr/local/bin/skip-htpc
install -m 0755 "${ROOT}/launch.sh" /usr/local/bin/launch.sh
install -d /etc/skip-htpc
if [[ ! -f /etc/skip-htpc/config.yaml ]]; then
  install -m 0644 "${ROOT}/config.yaml" /etc/skip-htpc/config.yaml
fi

if [[ ! -f /usr/share/xsessions/plasmax11.desktop ]]; then
  echo "plasma-session-x11 did not install /usr/share/xsessions/plasmax11.desktop" >&2
  exit 1
fi
install -d /etc/sddm.conf.d
sed "s/@HTPC_USER@/${HTPC_USER}/g" \
  "${ROOT}/install/sddm/skip-htpc.conf.in" \
  > /etc/sddm.conf.d/99-skip-htpc.conf
chmod 0644 /etc/sddm.conf.d/99-skip-htpc.conf
if [[ -x /usr/bin/sddm ]]; then
  printf '%s\n' /usr/bin/sddm > /etc/X11/default-display-manager
elif [[ -x /usr/sbin/sddm ]]; then
  printf '%s\n' /usr/sbin/sddm > /etc/X11/default-display-manager
fi
systemctl enable sddm
systemctl disable lightdm gdm gdm3 >/dev/null 2>&1 || true

install -d /var/lib/AccountsService/users
account_file=/var/lib/AccountsService/users/${HTPC_USER}
python3 - "$account_file" <<'PY'
import sys
from pathlib import Path
from skip_htpc.plasma import ensure_login_session

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8") if path.is_file() else ""
path.write_text(ensure_login_session(text), encoding="utf-8")
PY
chmod 0644 "$account_file"

install -d -o "$HTPC_USER" -g "$HTPC_USER" \
  "${HOME_DIR}/.config/autostart" \
  "${HOME_DIR}/.config" \
  "${HOME_DIR}/.local/share/applications" \
  "${HOME_DIR}/.kodi/userdata/keymaps"
install -m 0644 -o "$HTPC_USER" -g "$HTPC_USER" \
  "${ROOT}/session/autostart/skip-htpc.desktop" \
  "${HOME_DIR}/.config/autostart/skip-htpc.desktop"
install -m 0644 -o "$HTPC_USER" -g "$HTPC_USER" \
  "${ROOT}/session/plasma/skip-htpc-next.desktop" \
  "${HOME_DIR}/.local/share/applications/skip-htpc-next.desktop"
install -m 0644 -o "$HTPC_USER" -g "$HTPC_USER" \
  "${ROOT}/kodi/userdata/keymaps/skip-htpc.xml" \
  "${HOME_DIR}/.kodi/userdata/keymaps/skip-htpc.xml"

shortcut_file=${HOME_DIR}/.config/kglobalshortcutsrc
kwin_file=${HOME_DIR}/.config/kwinrc
python3 - "$shortcut_file" "$kwin_file" <<'PY'
import sys
from pathlib import Path
from skip_htpc.plasma import ensure_kwin, ensure_shortcut

shortcut = Path(sys.argv[1])
kwin = Path(sys.argv[2])
shortcut_text = shortcut.read_text(encoding="utf-8") if shortcut.is_file() else ""
kwin_text = kwin.read_text(encoding="utf-8") if kwin.is_file() else ""
shortcut.write_text(ensure_shortcut(shortcut_text), encoding="utf-8")
kwin.write_text(ensure_kwin(kwin_text), encoding="utf-8")
PY
chown "${HTPC_USER}:${HTPC_USER}" "$shortcut_file" "$kwin_file" \
  "${HOME_DIR}/.config" "${HOME_DIR}/.kodi" "${HOME_DIR}/.local"
chmod 0644 "$shortcut_file" "$kwin_file"

# The Plasma autostart entry is the boot path. The user unit is installed
# and left disabled so a login does not start Kodi a second time.
install -m 0644 "${ROOT}/session/autostart/skip-htpc.desktop" \
  /usr/share/applications/skip-htpc.desktop
install -d /usr/lib/systemd/user
install -m 0644 "${ROOT}/session/systemd/skip-htpc.service" \
  /usr/lib/systemd/user/skip-htpc.service

amd_driver=""
for dev in /sys/bus/pci/devices/*; do
  [[ -f "${dev}/vendor" && -f "${dev}/class" ]] || continue
  vendor=$(tr -d '[:space:]' < "${dev}/vendor")
  class=$(tr -d '[:space:]' < "${dev}/class")
  case "$class" in
    0x030000|0x030200|0x038000) ;;
    *) continue ;;
  esac
  [[ "$vendor" == "0x1002" ]] || continue
  if [[ -L "${dev}/driver" ]]; then
    amd_driver=$(basename "$(readlink "${dev}/driver")")
  fi
done
vainfo_text=""
if command -v vainfo >/dev/null 2>&1; then
  # The i7-3770's own GPU can be renderD128. Ask vainfo about the RX 580 node.
  amd_node=""
  for sysnode in /sys/class/drm/renderD*; do
    [[ -f "${sysnode}/device/vendor" && -f "${sysnode}/device/device" ]] || continue
    vendor=$(tr -d '[:space:]' < "${sysnode}/device/vendor")
    devid=$(tr -d '[:space:]' < "${sysnode}/device/device")
    [[ "$vendor" == "0x1002" ]] || continue
    case "$devid" in
      0x67df|0x6fdf) amd_node="/dev/dri/$(basename "$sysnode")" ;;
    esac
  done
  if [[ -n "$amd_node" ]]; then
    vainfo_text=$(LIBVA_DRIVER_NAME=radeonsi vainfo --display drm --device "$amd_node" 2>&1 || true)
  else
    vainfo_text=$(LIBVA_DRIVER_NAME=radeonsi vainfo --display drm 2>&1 || true)
  fi
fi
set +e
python3 -m skip_htpc gpu-ok --lspci "$gpu_text" --driver "$amd_driver" --vainfo "$vainfo_text"
gpu_code=$?
set -e
if [[ "$gpu_code" -eq 11 ]]; then
  echo "The RX 580 is not on amdgpu yet. Reboot before treating playback as ready." >&2
elif [[ "$gpu_code" -eq 12 || "$gpu_code" -eq 14 ]]; then
  echo "VA-API HEVC Main 10 was not confirmed. Reboot, then run: vainfo --display drm" >&2
fi

cat <<EOF

Installed. Reboot, then:

  1. Plug the TV into the RX 580. The 8-pin power plug is on the card's
     top edge, at the end opposite the video ports.
  2. Kodi should be on the TV. Settings → Player → Videos, expert level:
     VAAPI on, HEVC VAAPI on, render method VAAPI.
     Settings → System → Display: full screen, and "Use full screen window"
     so YouTube, Areena, and Netflix can be raised over Kodi.
  3. Press the spare Flirc key (F13). The cycle is
     Kodi → YouTube → Areena → Netflix.
  4. Sign in once with a keyboard. Each site keeps its own Chrome profile.
  5. Program the Flirc as a keyboard. Leave volume off it if the amp still
     hears those IR codes directly. See docs/remote.md.

System Settings → Power → leave the screen on. The session also turns DPMS off.
EOF
