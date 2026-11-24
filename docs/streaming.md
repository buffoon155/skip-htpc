# Netflix and Areena

Both sites run in the official web player. Do not install an unofficial Kodi Netflix add-on. Those add-ons break, and they are not the path this machine uses.

| App | Command | Window class | Profile |
| --- | --- | --- | --- |
| Netflix | `google-chrome --app=https://www.netflix.com` | `skip-htpc-netflix` | `~/.local/share/skip-htpc/profiles/netflix` |
| Areena | `google-chrome --app=https://areena.yle.fi` | `skip-htpc-areena` | `~/.local/share/skip-htpc/profiles/areena` |

Separate profiles mean both can stay open. `skip-htpc launch` focuses the existing window when the class is already on screen, and starts the browser only when it is not.

## Widevine

Install Google Chrome (`google-chrome-stable`). That package supplies the Widevine CDM. On Linux the CDM is L3, so Netflix tops out around 720p. Areena's web player uses the same browser. The GTX 660 does not change the CDM level.

`launch.sh` selects `google-chrome-stable`, then `google-chrome`, and only then `chromium` or `chromium-browser`. Chromium still accepts `--load-extension`, but the distro build often has no CDM, so Netflix does not play. The launcher treats a binary whose version string starts with `Google Chrome` as branded Chrome, and everything else as Chromium.

## Extension

`extension/` is an MV3 content script. It is not a web-store package.

Branded Chrome has ignored `--load-extension` since Chrome 137. The launcher starts Chrome with `--remote-debugging-pipe` and `--enable-unsafe-extension-debugging`, sends `Extensions.loadUnpacked` for this directory, and keeps the pipe open until Chrome exits. The pipe is a pair of file descriptors, not a TCP port. Do not add `--remote-debugging-port`.

On Chromium the same directory is passed as `--load-extension`.

While a `<video>` element covers most of the window, arrows, Enter, and Esc go to the player (seek and exit). While a text field is focused they go to the field, which is how the account login works. Otherwise the arrows move an orange ring and Enter clicks. Esc calls `history.back()`.

The script only matches `https://www.netflix.com/*` and `https://areena.yle.fi/*`.

## Kodi next to the browser

Kodi is started as a normal X client (`kodi`, not `kodi --standalone`). Standalone mode replaces the session and the launcher cannot put a browser on top of it. "Use full screen window" in Kodi's expert display settings is the other half of that: exclusive fullscreen also cannot be covered.

Logs from a browser start are in the profile directory (`chrome.log`, `supervisor.log`) and in `~/.local/state/skip-htpc/launcher.log`.
