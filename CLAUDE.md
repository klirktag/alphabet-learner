# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A single-page web app that teaches kids the alphabet. The whole screen is one big keyboard whose keys are arranged **alphabetically (A–Z), not QWERTY** — this is deliberate for pedagogical reasons; do not reorder them. Tapping/clicking a key, or pressing the corresponding physical key, plays a recording of that letter's name.

The same web app is also packaged as a native Android APK that bundles all assets and runs offline in a full-screen WebView ([android/](android/)). The primary deployment target is a child's tablet — **touch input is the main interaction**, not a mouse.

## Product constraints (do not change without asking)

- **Stack: plain HTML, CSS, JavaScript + jQuery only.** No build step, no bundler, no React/Vue/etc. jQuery is loaded from a CDN in [index.html](index.html).
- **Keyboard order is alphabetical**, laid out as 6 / 7 / 7 / 6 rows in [index.html](index.html). Keep it that way.
- **Keys fill the viewport.** Sizing uses `vmin` units in [style.css](style.css) so the keyboard scales to phones, tablets, and desktop without scrolling.
- **Visual style is colorful and child-friendly** (rounded keys, bright per-letter colors, playful font). Per-key colors are assigned via `.key[data-letter="x"]` selectors.
- **One sound per letter**, served from [sound/](sound/) as `a.mp4` … `z.mp4` (Opus codec in an MP4 container — see "Audio" below).
- **Touch is the primary input.** Click/mouse and physical-keyboard support are nice extras but the design target is finger taps on a tablet.

## Run the web version

No build, no dependencies to install. Just serve the directory:

```bash
python3 -m http.server 8000
# then open http://localhost:8000
```

Any static file server works. The app is fully client-side and works offline once loaded.

## Audio

The released sounds in [sound/](sound/) are **Opus-in-MP4**: short (≈0.4s), mono, 48 kHz, ~4 KB each (≈10× smaller than the WAV sources). They play on every modern Chromium-based browser and on Android WebView (API 21+).

The pristine espeak WAV recordings live under [sound/originals/](sound/originals/) — keep them so the MP4s can be regenerated losslessly with different codec settings.

**Regenerating the originals** (e.g. to change voice, speed, or pitch — re-run for all 26 so they stay consistent):

```bash
for L in A B C D E F G H I J K L M N O P Q R S T U V W X Y Z; do
  l=$(echo "$L" | tr A-Z a-z)
  espeak -v en-us+f3 -s 130 -p 60 -w "sound/originals/${l}.wav" "$L"
done
```

Flags: `-v en-us+f3` (US English, female variant 3), `-s 130` (slower than default for clarity), `-p 60` (slightly higher pitch).

**Regenerating the MP4s** from the originals:

```bash
for l in {a..z}; do
  ffmpeg -y -i "sound/originals/${l}.wav" \
      -c:a libopus -b:a 32k -vbr on -application voip \
      -f mp4 "sound/${l}.mp4"
done
```

If you change the file extension (e.g. switch to `.webm` or `.opus`), also update the `new Audio("sound/" + letter + ".mp4")` line in [script.js](script.js) and the asset-copy glob in [android/build.sh](android/build.sh).

## Web architecture in one minute

- [index.html](index.html) — static markup. One `<button class="key" data-letter="x">` per letter, grouped into `.row` divs. The `data-letter` attribute is the contract between HTML, CSS (per-key colors), JS (sound lookup), and the filesystem (`sound/x.mp4`).
- [style.css](style.css) — flex layout (`#keyboard` column → `.row` rows → flex-1 keys), `vmin`-based sizing, and per-letter background colors. A `.pressed` class provides the press-down animation. `touch-action: manipulation` + `user-select: none` keep taps snappy and free of accidental selection or double-tap-zoom.
- [script.js](script.js) — on DOM ready, builds a `sounds` map of pre-loaded `Audio` objects keyed by letter, then wires two input paths to the same `playLetter` + `flash` pair:
  1. `pointerdown` on `.key` (covers mouse, touch, and pen in a single handler — preferred over `click` because it fires immediately on finger-down, avoiding click latency).
  2. `keydown` on `document` for physical A–Z keys, which looks up the matching button via `data-letter` so the visual press animation also fires.

  `audio.currentTime = 0` before `play()` so rapid repeat taps always restart the sound from the beginning.

## Android app

The [android/](android/) directory wraps the web app in a single-Activity full-screen WebView, packaged as a self-contained APK with all HTML/CSS/JS/audio assets bundled (no network needed at runtime).

**Build, install, and launch on a connected device:**

```bash
./android/build.sh run        # build → adb install → adb launch
./android/build.sh install    # build → adb install
./android/build.sh            # build only; APK at android/build/alphabet-learner.apk
```

The build script drives the Android SDK tools directly (`aapt2`, `d8`, `apksigner`, `zipalign`) and **does not require Gradle or the Android Gradle Plugin**. This keeps the project zero-dependency for a tiny WebView wrapper — if the app ever grows beyond a single Activity or needs androidx, switch to Gradle.

The first build generates `android/debug.keystore` (gitignored). Keep that file on the machine you build from — if it gets deleted, the next build creates a new one and you'll have to uninstall before reinstalling (signature mismatch).

Defaults assume `ANDROID_HOME=/home/ekirprivat/android-sdk`, build-tools 36.0.0, and platform android-36. Override via env vars (`SDK`, `BUILD_TOOLS_VER`, `PLATFORM_VER`) at the top of [android/build.sh](android/build.sh).

### Android architecture

- [android/AndroidManifest.xml](android/AndroidManifest.xml) — package `com.example.alphabetlearner`, single launcher Activity, no permissions (audio is local, no network). `configChanges` covers everything that could otherwise destroy and recreate the WebView (orientation, keyboard, density…).
- [android/src/com/example/alphabetlearner/MainActivity.java](android/src/com/example/alphabetlearner/MainActivity.java) — creates a WebView, enables JS + DOM storage, calls `setMediaPlaybackRequiresUserGesture(false)` (essential: otherwise the first tap on each letter wouldn't play sound), disables long-press / scroll bounce / zoom, loads `file:///android_asset/index.html`, and re-applies immersive sticky fullscreen on every focus gain.
- [android/res/](android/res/) — `strings.xml`, `colors.xml`, fullscreen `AppTheme` (no action bar, transparent status/nav bars), and an adaptive launcher icon (white "A" on the app's blue) defined entirely in XML (no PNGs).
- [android/build.sh](android/build.sh) — pipeline: copy web assets → `aapt2 compile` → `aapt2 link` (manifest + resources + assets → unsigned APK + R.java) → `javac` → `d8` → zip classes.dex into the APK → `zipalign` → `apksigner sign`. Output: `android/build/alphabet-learner.apk`.

### Touch handling (the primary input path)

Three layers cooperate to make taps feel instant on the tablet:

1. **CSS** ([style.css](style.css)) — `touch-action: manipulation` disables double-tap-zoom (the source of the legacy 300ms tap delay); `user-select: none` and `-webkit-tap-highlight-color: transparent` keep finger drags from selecting text or flashing the system highlight; the press animation is driven by a `.pressed` class added in JS, not by `:active`, so it works identically on mouse and touch.
2. **JS** ([script.js](script.js)) — uses `pointerdown` (not `click`) so the sound fires on finger-down with no waiting period.
3. **WebView** ([android/src/com/example/alphabetlearner/MainActivity.java](android/src/com/example/alphabetlearner/MainActivity.java)) — disables long-click, haptics, scroll bars, and over-scroll glow so nothing in the host competes with the page's tap handling; `setMediaPlaybackRequiresUserGesture(false)` lets `Audio.play()` succeed from those pointerdowns without WebView gating.

If touch ever feels laggy or "double", check these three places first.

## Workflow

The product spec asks for a commit after each change and to start the app to try it out. Follow that: small, focused commits, and serve the directory locally (or rebuild and `adb install` the APK) to verify visually/audibly before reporting work done.
