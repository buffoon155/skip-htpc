# Remote

The Skip remote talks to a Flirc USB receiver. The Flirc is a normal keyboard. This session does not grab the device, and there is no udev rule in this repo. An exclusive evdev grab would swallow the keys before the session sees them.

Program the Flirc with the Flirc GUI, Full Keyboard layout, the same way the arrows and transport keys are already programmed:

| Remote | Flirc | Who handles it |
| --- | --- | --- |
| Up / Down / Left / Right | Arrow keys | Kodi, YouTube TV, or the spatial-navigation extension |
| OK | Enter | Select / click |
| Back | Esc | Kodi Back, or browser history |
| Play, pause, next, previous, stop | Media keys | Passed through. Kodi and Chrome both understand them. |
| Spare key | F13 | Plasma runs `/usr/local/bin/launch.sh next` |

Leave volume and mute off the Flirc when those buttons still need to reach an amplifier by infrared. A code recorded into the Flirc is consumed by the dongle and the amplifier does not hear it.

F13 is debounced for a third of a second so a held key does not spin through every app. The order is Kodi → YouTube → Areena → Netflix → Kodi. If the focused window is a terminal or something else outside that list, the next press continues from the last app the launcher started.

Plasma 6 stores that shortcut in two files, written by the installer:

`~/.local/share/applications/skip-htpc-next.desktop` runs `launch.sh next` and is marked `X-KDE-GlobalAccel-CommandShortcut=true`.

`~/.config/kglobalshortcutsrc` holds:

```ini
[services][skip-htpc-next.desktop]
_launch=F13,none,Skip HTPC next
```

Plasma reads both at login. A later run of the installer puts F13 back if the group was edited. `skip-htpc patch-plasma <kglobalshortcutsrc>` does the same edit on its own.

Kodi's own keymap no-ops F13 in case the grab is missing. Arrows, Enter, Esc, and the media keys stay on Kodi's defaults.

The session turns DPMS and the X screensaver off. Pause still leaves a picture on the TV; turn the TV off when you leave the room. Plasma's own power settings can still blank the panel, so System Settings → Power should leave the screen on.
