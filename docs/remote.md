# Remote

The Skip remote talks to a Flirc USB receiver. The Flirc is a normal keyboard. This session does not grab the device, and there is no udev rule in this repo. An exclusive evdev grab would swallow the keys before X sees them.

Program the Flirc with the Flirc GUI, Full Keyboard layout, the same way the arrows and transport keys are already programmed:

| Remote | Flirc | Who handles it |
| --- | --- | --- |
| Up / Down / Left / Right | Arrow keys | Kodi, or the spatial-navigation extension |
| OK | Enter | Select / click |
| Back | Esc | Kodi Back, or browser history |
| Play, pause, next, previous, stop | Media keys | Passed through. Kodi and Chrome both understand them. |
| Spare key | F13 | Openbox runs `/usr/local/bin/skip-htpc cycle` |

Leave volume and mute off the Flirc when those buttons still need to reach an amplifier by infrared. A code recorded into the Flirc is consumed by the dongle and the amplifier does not hear it.

F13 is debounced for a third of a second so a held key does not spin through every app. The order is Kodi → Netflix → Areena → Kodi. If the focused window is a terminal or something else outside that list, the next press continues from the last app the launcher started.

Openbox inserts this into `~/.config/openbox/rc.xml` (the installer patches the file, including on a later run):

```xml
<keybind key="F13">
  <action name="Execute">
    <command>/usr/local/bin/skip-htpc cycle</command>
  </action>
</keybind>
```

Kodi's own keymap no-ops F13 in case the grab is missing. Arrows, Enter, Esc, and the media keys stay on Kodi's defaults.

The session turns DPMS and the X screensaver off. Pause still leaves a picture on the TV; turn the TV off when you leave the room.

A right-click on the desktop opens Kodi, Netflix, Areena, a terminal, and Exit. That menu is for a keyboard on the coffee table, not for the remote.
