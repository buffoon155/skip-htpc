# Install

Do this on the spare PC, not on a machine you use as a daily desktop. `--yes` switches the display manager to LightDM and autologins the `htpc` account into Openbox.

## Base system

Install Ubuntu 22.04 amd64 and update it. Hold the kernel on 5.15 or 6.8 if a later HWE kernel is offered (see [hardware.md](hardware.md)).

```bash
git clone https://github.com/buffoon155/skip-htpc.git
cd skip-htpc
sudo ./install/install.sh --dry-run
sudo ./install/install.sh --yes --nvidia
sudo reboot
```

`--dry-run` is the default and changes nothing. `--yes` installs:

- Openbox, LightDM, Xorg, distro Kodi, wmctrl, xdotool
- Google Chrome stable. Prefer Chrome over Chromium: Chrome ships Widevine, and Netflix needs that CDM. Chromium is only a fallback when `google-chrome-stable` is absent.
- user `htpc` (override with `HTPC_USER=something sudo ./install/install.sh --yes`)
- `/usr/local/bin/launch.sh`, `/usr/local/bin/skip-htpc`, and `/usr/local/share/skip-htpc`
- LightDM autologin to the Openbox session
- the F13 keybind in that user's Openbox config
- the Kodi keymap under that user's `.kodi`

`--nvidia` is separate because a wrong driver blanks the display. Skip it to keep the current driver (Nouveau is fine for a first boot). `--no-chrome` skips Google's apt repository; point `browser` at another binary afterwards.

The script does not restart the display manager. Reboot when you are ready for the TV to come up as `htpc`.

## First boot

1. Kodi opens on the library screen.
2. Settings → System → Display. Set the settings level to Expert. Use full screen, and turn on **Use full screen window**. Exclusive fullscreen cannot be covered by Netflix or Areena.
3. Player → Videos: render method VDPAU or Automatic.
4. Add the library sources in Kodi. They are not in this repo.
5. Press F13, or the spare Flirc key, once. That runs `launch.sh next` and opens Netflix in Chrome (`--app=https://www.netflix.com`). Sign in with a USB keyboard. Press F13 again for Areena (`--app=https://areena.yle.fi`). The Chrome profiles are kept under `~/.local/share/skip-htpc/profiles/`.
6. `skip-htpc doctor` should report the extension, the browser, and wmctrl.

## Config

Optional files, merged in this order: `/etc/skip-htpc/config.json`, `~/.config/skip-htpc/config.json`, then `SKIP_HTPC_CONFIG`.

```json
{
  "browser": "/usr/bin/chromium",
  "audio_sink": "alsa_output.pci-0000_01_00.1.hdmi-stereo"
}
```

An `apps` array replaces the whole cycle list. Each browser app needs an `https://` URL and a window class. The defaults are Kodi, Netflix, Areena.

## Checks

```bash
skip-htpc apps
skip-htpc doctor
skip-htpc launch netflix
skip-htpc which
skip-htpc cycle
nvidia-smi
```

`nvidia-smi` should report a 470.x driver after `--nvidia` and a reboot. If the screen stays black, boot to a text console from GRUB and use the Nouveau recovery in [hardware.md](hardware.md).
