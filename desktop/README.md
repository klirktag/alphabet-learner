# Desktop app (Electron)

A thin Electron wrapper around the same [index.html](../index.html) /
[style.css](../style.css) / [script.js](../script.js) web app the browser and
Android versions use — no changes to the web app itself. Built for a
toddler's desktop: **always fullscreen**, no menu bar, no window management
to stumble into, and exiting always goes through a confirm dialog.

## Exit behavior

The intended user can't do window management, so accidental exits need to be
hard while an adult's exit stays easy:

- The window is always fullscreen (`main.js` snaps it back if anything ever
  knocks it out) — no title bar, no visible close button.
- Reload (Ctrl/Cmd+R, F5), devtools (Ctrl/Cmd+Shift+I, F12), and toggling
  fullscreen (F11) are swallowed — keys a toddler mashing the keyboard could
  plausibly hit.
- **Alt+Tab is untouched** — it's handled entirely by the window manager,
  Electron never sees it.
- Quitting — via Alt+F4, the window manager's own close action, or the
  **Ctrl+Escape** shortcut — always shows a "Quit ABC App?" confirm dialog.
  There is no single keystroke or click that exits the app.

## Held-key repeat

A held physical key should trigger the letter sound once, not repeat it for
as long as it's down. The web app's own `keydown` handler already guards
against this with the standard `if (e.repeat) return;` — but on this
Electron/Linux build, `KeyboardEvent.repeat` in the renderer is unreliable
(observed always `undefined`, even mid-hold), so that guard alone doesn't
work here. `main.js`'s `before-input-event` handler filters on
`input.isAutoRepeat` instead — which *is* correct at the main-process level —
and calls `event.preventDefault()` so repeat keydowns never reach the page at
all. Verified by simulating a real held key via X11/XTest and confirming
exactly one event reaches the renderer regardless of hold duration.

## Run it (dev)

```bash
cd desktop
npm install   # first time only
npm start     # bundles assets into app/, then launches Electron
```

`npm start` re-copies the web assets every time (`npm run assets` →
[build-assets.sh](build-assets.sh)), so edits to the root `index.html` /
`style.css` / `script.js` / `audio-packs/` show up on the next launch — no
separate build step to remember.

## Build a flatpak

Packaging lives entirely under [flatpak/](flatpak/), separate from the
Electron app source. It uses electron-builder's flatpak target, which rides
on the official `org.electronjs.Electron2.BaseApp` shared runtime — no
hand-written flatpak manifest to maintain.

One-time setup (system-level, so not scripted):

```bash
flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
flatpak install --user flathub org.freedesktop.Platform//24.08 \
    org.freedesktop.Sdk//24.08 org.electronjs.Electron2.BaseApp//24.08
```

Then:

```bash
cd desktop
./flatpak/build.sh      # bundles assets + runs electron-builder -> flatpak/dist/*.flatpak
./flatpak/install.sh    # flatpak install --user the bundle just built
flatpak run se.ekirprivat.abcapp
./flatpak/uninstall.sh  # when you want it gone
```

`flatpak/electron-builder.yml` holds the flatpak-specific config (app ID,
finish-args for X11/Wayland + PulseAudio + GPU, output directory). Paths in
it resolve against `desktop/` (where `build.sh` runs electron-builder from),
not against `flatpak/` itself.

## Flatpak sandbox gotchas (already fixed, documented so they don't get re-broken)

Three non-obvious things bit us building this, all now baked into the config/code:

- **`baseVersion` vs `runtimeVersion`**: electron-builder's flatpak target defaults `org.electronjs.Electron2.BaseApp`'s version to `20.08` *independently* of the `runtimeVersion` you set for the Platform/Sdk — setting only `runtimeVersion` silently leaves you pulling the wrong (likely uninstalled) BaseApp. `flatpak/electron-builder.yml` pins both to `24.08`.
- **GPU crashes inside the sandbox**: Chromium's GPU process failed to initialize inside the flatpak sandbox on the machine this was built on (host driver/Mesa vs. the runtime's Mesa), producing a fullscreen window with zero content — no crash, no error, just blank. `main.js` calls `app.disableHardwareAcceleration()` unconditionally to sidestep this; harmless for a UI this simple.
- **D-Bus abort**: without `--socket=session-bus` in `finishArgs`, Chromium's D-Bus probe (used for things like power-monitor/keyring integration this app never touches) fails with a **fatal** abort, not a soft error — the window never appears. If you ever trim `finishArgs`, keep this one.

If you build/install from a terminal opened inside VS Code, its snap can leak `XDG_DATA_HOME`/`XDG_DATA_DIRS` pointing at VS Code's own private data dir, silently redirecting `flatpak` commands to `~/snap/code/<rev>/.local/share/flatpak` instead of the real `~/.local/share/flatpak`. `flatpak/build.sh`/`install.sh`/`uninstall.sh` all `unset` these themselves — do the same for any ad-hoc `flatpak` command you run by hand.

## Files

- [main.js](main.js) — Electron main process: fullscreen window, no menu,
  the exit-lockdown logic above.
- [build-assets.sh](build-assets.sh) — copies the web app + vendored jQuery
  + every `audio-packs/<lang>-<source>/*.webm` (skipping `originals/*.wav`)
  into `app/` (gitignored, regenerated on every `npm start` / flatpak
  build). Mirrors [../android/build.sh](../android/build.sh)'s asset
  bundling.
- [icon.png](icon.png) — app icon (white "A" on the same blue as the
  Android launcher icon), generated with ImageMagick, not hand-drawn.
- [flatpak/](flatpak/) — flatpak packaging: `electron-builder.yml`,
  `build.sh`, `install.sh`, `uninstall.sh`. `flatpak/dist/` (build output)
  is gitignored.
