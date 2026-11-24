# Install

Do this on the spare PC after Kubuntu 26.04 is installed, not on a machine you use as a daily desktop. `--yes` switches SDDM to autologin the `htpc` account into Plasma (X11).

## Base system

Install Kubuntu 26.04 amd64 and update it. Kubuntu 26.10 is also accepted. Leave the kernel on the distro's current version (see [hardware.md](hardware.md)).

```bash
git clone https://github.com/buffoon155/skip-htpc.git
cd skip-htpc
sudo ./install/install.sh --dry-run
sudo ./install/install.sh --yes
sudo reboot
```

`--dry-run` is the default and changes nothing. `--yes` installs:

- `plasma-session-x11`, SDDM autologin, and Xorg
- `mesa-libgallium`, `vainfo`, `linux-firmware`, distro Kodi
- wmctrl, xdotool, pactl (`pulseaudio-utils` works with PipeWire)
- Google Chrome stable. Prefer Chrome over Chromium: Chrome ships Widevine, and Netflix needs that CDM. Chromium is only a fallback when `google-chrome-stable` is absent.
- user `htpc` (override with `HTPC_USER=something sudo ./install/install.sh --yes`)
- `/usr/local/bin/launch.sh`, `/usr/local/bin/skip-htpc`, and `/usr/local/share/skip-htpc`
- SDDM autologin to session `plasmax11`
- the F13 shortcut in that user's Plasma config
- the Kodi keymap under that user's `.kodi`
- the account in the `render`, `video`, `audio`, and `input` groups when those groups exist

`--no-chrome` skips Google's apt repository; point `browser` at another binary afterwards.

The script leaves the login session alone when `lspci` shows a display GPU and none of the lines is an Ellesmere RX 580 (`1002:67df` or `1002:6fdf`). A machine with no display device at all still gets the session files, so the check can be read on its own with `skip-htpc gpu-ok`.

The script does not restart the display manager. Reboot when you are ready for the TV to come up as `htpc`.

## Boot

SDDM autologins `htpc` into Plasma (X11). `~/.config/autostart/skip-htpc.desktop` runs `session/plasma/session.sh`, which selects the HDMI sink and runs `launch.sh kodi`. That is the path that has `DISPLAY`.

The F13 shortcut is `~/.local/share/applications/skip-htpc-next.desktop` plus a group in `~/.config/kglobalshortcutsrc`. Plasma reads both at login.

One extra is copied and left disabled:

- `/usr/lib/systemd/user/skip-htpc.service`. On a session that already has `DISPLAY`:

```bash
systemctl --user enable --now skip-htpc.service
```

`loginctl enable-linger htpc` is not required. The TV always has a login. Enabling the user unit and the Plasma autostart entry together starts Kodi twice; `launch.sh` focuses a window that is already open, so wait until Kodi's window exists before treating a second start as a failure.

## First boot

1. The HDMI cable is in the RX 580, and the 8-pin power plug is seated.
2. Kodi opens on the library screen.
3. Settings → System → Display. Set the settings level to Expert. Use full screen, and turn on **Use full screen window**. Exclusive fullscreen cannot be covered by YouTube, Areena, or Netflix.
4. Player → Videos, expert level: allow VAAPI, turn on HEVC VAAPI, render method VAAPI.
5. System Settings → Power: leave the screen on. The session script also turns DPMS off with `xset`.
6. Add the library sources in Kodi. They are not in this repo. The files live on the other machine.
7. Press F13, or the spare Flirc key, once. That runs `launch.sh next` and opens YouTube TV in Chrome (`--app=https://www.youtube.com/tv`). Sign in with a USB keyboard. The next press opens Areena (`--app=https://areena.yle.fi`), then Netflix (`--app=https://www.netflix.com`). The Chrome profiles are kept under `~/.local/share/skip-htpc/profiles/`.
8. `skip-htpc doctor` should report the extension, the browser, and wmctrl. `vainfo --display drm` should list `VAProfileHEVCMain10`.

## Config

`launch.sh` reads `config.yaml` (`cycle_order: [kodi, youtube, areena, netflix]`, plus the three site URLs). The installer copies it to `/etc/skip-htpc/config.yaml` when that file is absent.

The Python launcher still reads JSON, merged in this order: `/etc/skip-htpc/config.json`, `~/.config/skip-htpc/config.json`, then `SKIP_HTPC_CONFIG`. `launch.sh` passes the YAML URLs through as `SKIP_HTPC_YOUTUBE_URL`, `SKIP_HTPC_AREENA_URL`, and `SKIP_HTPC_NETFLIX_URL`.

```json
{
  "browser": "/usr/bin/chromium",
  "audio_sink": "alsa_output.pci-0000_01_00.1.hdmi-stereo"
}
```

An `apps` array replaces the whole cycle list. Each browser app needs an `https://` URL and a window class. The defaults are Kodi, YouTube, Areena, Netflix.

## Checks

```bash
skip-htpc apps
skip-htpc doctor
skip-htpc launch youtube
skip-htpc which
skip-htpc cycle
vainfo --display drm
```

`vainfo` should show `VAProfileHEVCMain10` with `VAEntrypointVLD` after the reboot. `skip-htpc gpu-ok` prints the same conclusion from an `lspci` dump, a driver name, and a `vainfo` dump.
