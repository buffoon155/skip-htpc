# YouTube, Areena, and Netflix

YouTube, Areena, and Netflix run in the official web player. The official sites are the path this machine uses.

| App | Command | Window class | Profile |
| --- | --- | --- | --- |
| YouTube | `google-chrome --app=https://www.youtube.com/tv` | `skip-htpc-youtube` | `~/.local/share/skip-htpc/profiles/youtube` |
| Areena | `google-chrome --app=https://areena.yle.fi` | `skip-htpc-areena` | `~/.local/share/skip-htpc/profiles/areena` |
| Netflix | `google-chrome --app=https://www.netflix.com` | `skip-htpc-netflix` | `~/.local/share/skip-htpc/profiles/netflix` |

`https://www.youtube.com/tv` is the 10-foot YouTube site (Leanback). Separate profiles mean all three can stay open. `skip-htpc launch` focuses the existing window when the class is already on screen, and starts the browser only when it is not.

## Widevine

Install Google Chrome (`google-chrome-stable`). That package supplies the Widevine CDM. On Linux the CDM is L3, so Netflix tops out around 720p. Areena's web player uses the same browser. The RX 580 does not change the CDM level. Kodi can use the card's HEVC Main 10 decoder; Netflix in Chrome does not get a higher security level. YouTube TV can use the card's VP9 decoder through VA-API.

`launch.sh` selects `google-chrome-stable`, then `google-chrome`, and only then `chromium` or `chromium-browser`. Chromium still accepts `--load-extension`, but the distro build often has no CDM, so Netflix does not play. The launcher treats a binary whose version string starts with `Google Chrome` as branded Chrome, and everything else as Chromium.

Chrome is started with a single features line:

```text
--enable-features=AcceleratedVideoDecodeLinuxGL,AcceleratedVideoDecodeLinuxZeroCopyGL
--use-gl=desktop
```

`LIBVA_DRIVER_NAME=radeonsi` is set for that process. After a video starts, `chrome://gpu` should show hardware video decode. `chrome://media-internals` names `GpuVideoDecoder` on a decoded stream.

## Extension

`extension/` is an MV3 content script. It is not a web-store package.

Branded Chrome has ignored `--load-extension` since Chrome 137. The launcher starts Chrome with `--remote-debugging-pipe` and `--enable-unsafe-extension-debugging`, sends `Extensions.loadUnpacked` for this directory, and keeps the pipe open until Chrome exits. The pipe is a pair of file descriptors, not a TCP port. Do not add `--remote-debugging-port`.

On Chromium the same directory is passed as `--load-extension`.

While a `<video>` element covers most of the window, arrows, Enter, and Esc go to the player (seek and exit). While a text field is focused they go to the field, which is how the account login works. Otherwise the arrows move an orange ring and Enter clicks. Esc calls `history.back()`.

The script matches `https://www.netflix.com/*` and `https://areena.yle.fi/*`. It does not match `youtube.com`. YouTube TV already moves with the arrow keys, and the orange ring would take those keys away from it.

## Kodi next to the browser

Kodi is started as a normal X client (`kodi`, not `kodi --standalone`). Standalone mode replaces the session and the launcher cannot put a browser on top of it. "Use full screen window" in Kodi's expert display settings is the other half of that: exclusive fullscreen also cannot be covered.

Logs from a browser start are in the profile directory (`chrome.log`, `supervisor.log`) and in `~/.local/state/skip-htpc/launcher.log`.
