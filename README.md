# skip-htpc

Living-room HTPC for a spare AMD64 PC with a GeForce GTX 660.

Kodi plays the local library. Netflix and Yle Areena run in Chrome `--app` windows, on the official sites, with Widevine. A Flirc turns the Skip remote into a keyboard. F13 cycles Kodi, Netflix, and Areena.

This PC does not join any other home-theatre controller. There is no hub, serial amplifier control, or second-screen kiosk in this repository.

## What you get

| Piece | Role |
| --- | --- |
| Kodi | Native player for the library. Not used for Netflix. |
| Chrome `--app` | `https://www.netflix.com/browse` and `https://areena.yle.fi/` |
| `extension/` | MV3 spatial navigation for those two sites |
| `skip-htpc` | Focus or launch an app; F13 cycles them |
| Openbox + LightDM | Autologin session so the TV has one full-screen window |

Linux Widevine is the L3 CDM. Expect about 720p from Netflix, not 1080p or 4K. The GTX 660 decodes H.264 in Kodi and does not decode HEVC, VP9, or AV1 in hardware.

## Layout

```text
skip_htpc/          launcher, window matching, Chrome startup, audio
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
skip-htpc launch kodi|netflix|areena
skip-htpc cycle
skip-htpc audio
skip-htpc which
skip-htpc apps
skip-htpc doctor
```

From a checkout, the same commands are `python3 -m skip_htpc ...`.

## Tests

```bash
make test
```

The spatial-navigation tests and the launcher tests run here. Signing into Netflix, playing a title, and focusing Kodi with the real remote has to be done on the HTPC.
