# skip-htpc

Living-room HTPC for a spare AMD64 PC with a GeForce GTX 660.

Kodi plays the local library. Netflix and Yle Areena run in Google Chrome `--app` windows, on the official sites, with Widevine. A Flirc turns the Skip remote into a keyboard. F13 runs `launch.sh next`.

This PC does not join any other home-theatre controller. There is no hub, serial amplifier control, or second-screen kiosk in this repository.

## What you get

| Piece | Role |
| --- | --- |
| Kodi | Native player for the library. Not used for Netflix. |
| Chrome `--app` | `https://www.netflix.com` and `https://areena.yle.fi` |
| `launch.sh` | `kodi`, `netflix`, `areena`, `next`, `status` |
| `extension/` | MV3 spatial navigation for those two sites |
| Openbox + LightDM | Autologin session so the TV has one full-screen window |

Use **Google Chrome** (`google-chrome-stable`). It is the browser that ships the Widevine CDM. `launch.sh` picks Chrome before Chromium. Distro Chromium often has no CDM, and Netflix will not play there. Linux Widevine is L3, so Netflix stays around 720p. The GTX 660 decodes H.264 in Kodi and does not decode HEVC, VP9, or AV1 in hardware.

## Layout

```text
launch.sh           kodi | netflix | areena | next | status
config.yaml         cycle_order: [kodi, netflix, areena]
skip_htpc/          window focus, Chrome startup, audio
extension/          MV3 content script (spatial.js is the tested part)
session/openbox/    autostart, menu, F13 key inserted into rc.xml
kodi/userdata/      keymap that no-ops F13
install/            installer for the HTPC (dry-run unless --yes)
docs/               hardware, install, remote, streaming
```

## Install

On Ubuntu 22.04 on the HTPC:

```bash
sudo ./install/install.sh --yes --nvidia
sudo reboot
```

`--yes` alone installs the session and Chrome and leaves the display driver alone. Read [docs/hardware.md](docs/hardware.md) before `--nvidia`: the GTX 660 only works with the NVIDIA 470 branch, and a newer driver will not bring the desktop up.

Details: [docs/install.md](docs/install.md), [docs/remote.md](docs/remote.md), [docs/streaming.md](docs/streaming.md).

## Commands

```text
./launch.sh kodi|netflix|areena|next|status
```

`next` is what F13 runs. `status` prints the cycle order and which browser would open Netflix. Chrome is first; Chromium is used only when Chrome is not installed.

```bash
./scripts/selftest.sh
```

## Tests

```bash
make test
```

The spatial-navigation tests and the launcher tests run here. Signing into Netflix, playing a title, and focusing Kodi with the real remote has to be done on the HTPC.
