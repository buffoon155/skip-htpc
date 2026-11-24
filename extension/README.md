# Spatial navigation

MV3 content script for `https://www.netflix.com/*` and `https://areena.yle.fi/*`.

Arrow keys move an orange ring to the nearest link, button, or tab stop. Enter activates it. Esc goes back. While a video fills most of the window, the keys are left to the site's own player (seek, exit playback). The same is true while a text field is focused, so the one-time account login still works from a keyboard.

Branded Chrome ignores `--load-extension` since Chrome 137. The launcher loads this directory with `Extensions.loadUnpacked` over Chrome's debugging pipe. Chromium still gets `--load-extension`.

```bash
node --test extension/spatial.test.mjs
```
