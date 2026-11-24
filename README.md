# skip-htpc

Living-room HTPC for a spare AMD64 PC: Intel Core i7-3770 and an Asus Dual Radeon RX 580 4 GB.

Kodi plays the library from the Jellyfin server on another machine. YouTube, Yle Areena, and Netflix run in Google Chrome `--app` windows, on the official sites. A Flirc turns the Skip remote into a keyboard. F13 runs `launch.sh next`.

This PC does not join any other home-theatre controller. There is no hub, serial amplifier control, or second-screen kiosk in this repository.

## What you get

| Piece | Role |
| --- | --- |
| Kodi | Native player for the library. VA-API on the RX 580, including 10-bit HEVC. |
| Chrome `--app` | YouTube TV, `https://areena.yle.fi`, and `https://www.netflix.com` |
| `launch.sh` | `kodi`, `youtube`, `areena`, `netflix`, `next`, `status` |
| `extension/` | MV3 spatial navigation for Areena and Netflix |
| Plasma (X11) + SDDM | Autologin session so the TV has one full-screen window |

Use **Google Chrome** (`google-chrome-stable`). It is the browser that ships the Widevine CDM. `launch.sh` picks Chrome before Chromium. Distro Chromium often has no CDM, and Netflix will not play there. Linux Widevine is L3, so Netflix stays around 720p. The RX 580 decodes H.264, HEVC Main 10, and VP9. AV1 stays on the CPU. Widevine on Linux stays at L3.

YouTube opens at `https://www.youtube.com/tv`, the 10-foot site. That page already understands the remote, so the spatial-navigation extension stays off it.

## Layout

```text
launch.sh           kodi | youtube | areena | netflix | next | status
config.yaml         cycle_order: [kodi, youtube, areena, netflix]
skip_htpc/          window focus, Chrome startup, audio, GPU check
extension/          MV3 content script (spatial.js is the tested part)
session/plasma/     X11 session script and the F13 shortcut
session/autostart/  Plasma autostart entry (the boot path)
session/systemd/    optional user unit, not enabled by the installer
kodi/userdata/      keymap that no-ops F13
install/            installer for the HTPC (dry-run unless --yes)
docs/               hardware, install, remote, streaming
```

## Install

On Kubuntu 26.04 LTS on the HTPC (26.10 is also accepted):

```bash
sudo ./install/install.sh --yes
sudo reboot
```

The installer logs `htpc` into Plasma (X11) and installs the Mesa VA-API driver for the RX 580. Kubuntu's own default is a Wayland session; this machine uses the X11 session so `wmctrl` can raise Kodi and Chrome. Read [docs/hardware.md](docs/hardware.md) before the first reboot.

Details: [docs/install.md](docs/install.md), [docs/remote.md](docs/remote.md), [docs/streaming.md](docs/streaming.md).

## Commands

```text
./launch.sh kodi|youtube|areena|netflix|next|status
```

`next` is what F13 runs. The cycle is Kodi → YouTube → Areena → Netflix → Kodi. `status` prints the cycle order and which browser would open the sites. Chrome is first; Chromium is used only when Chrome is not installed.

```bash
./scripts/selftest.sh
```

## Tests

```bash
make test
```

The spatial-navigation tests and the launcher tests run here. Signing into YouTube, Areena, and Netflix, playing a title, and focusing Kodi with the real remote has to be done on the HTPC.
