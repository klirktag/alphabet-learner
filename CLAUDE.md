# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A single-page web app that teaches kids the alphabet — built first for the project owner's Swedish-speaking child. The whole screen is one big keyboard whose keys are arranged **alphabetically, not QWERTY** — this is deliberate for pedagogical reasons; do not reorder them. Tapping a key (or pressing the matching physical key) plays a recording of the letter's name in the active language.

The same web app is also packaged as a native Android APK ([android/](android/)) that bundles every asset and runs offline in a full-screen WebView. The primary deployment target is the kid's tablet — **touch is the main interaction**, not a mouse.

## Product constraints (do not change without asking)

- **Stack: plain HTML, CSS, JavaScript + jQuery only.** No build step for the web side, no bundler, no React/Vue/etc. jQuery is **vendored** at [vendor/jquery-3.7.1.min.js](vendor/jquery-3.7.1.min.js); the page loads it from there. Do not switch back to a CDN — Android WebView pages loaded from `file://` fail to fetch CDN scripts, and the whole app dies silently because every handler lives inside `$(function(){…})`.
- **Keyboard order is alphabetical**, with rows defined per-language in [script.js](script.js) (Swedish: 7/8/7/7, English: 6/7/7/6). Keep it that way.
- **Keys fill the viewport.** Sizing uses `vmin` units in [style.css](style.css) so the keyboard scales to phones, tablets, and desktop without scrolling.
- **Visual style is colorful and child-friendly** (rounded keys, bright per-letter colors, playful font). Per-key colors are assigned via `.key[data-letter="x"]` selectors, cycling through ~9 hues. Å, Ä, Ö continue the cycle.
- **One sound per letter**, served from [sound/](sound/) as Opus-in-WebM (~4 KB each). Audio objects are pre-created on load so playback is instant.
- **Touch is the primary input.** Click/mouse and physical-keyboard support are nice extras but the design target is finger taps on a tablet.

## Language configuration

The active language is a constant in [script.js](script.js):

```js
var LANG = "sv";  // change to "en" (or any key in ALPHABETS)
```

`ALPHABETS` is keyed by language code and contains:

- `letters` — the alphabet as a single lowercase string (the keyboard renders them in this order).
- `rows` — array of row lengths, must sum to `letters.length`.
- `slugs` — map from unicode letter to ASCII filename slug (only needed when a letter can't safely be a filename, e.g. `å → aa`, `ä → ae`, `ö → oe`).

To add a language: add an entry to `ALPHABETS`, create `sound/<code>/` with one WebM per slug (and its WAV original under `sound/<code>/originals/`), and `LANG` can now select it. A real in-app settings UI will replace the constant later — keep the schema simple so swapping out the constant for a getter is trivial.

## Run the web version

No build, no dependencies. Just serve the directory:

```bash
python3 -m http.server 8000
# then open http://localhost:8000
```

Browser compatibility: Firefox, Chrome/Chromium, Brave, and Android WebView all play Opus-in-WebM. Safari does not, but Safari isn't a target here. **Do not switch the audio container back to MP4** — Firefox refuses to play Opus-in-MP4 (codec OK, container not). That bit us before.

## Audio

Filed under [sound/](sound/) per language:

```
sound/
├── en/
│   ├── originals/  *.wav     # raw espeak recordings
│   └── *.webm                # Opus, mono 48 kHz, ~32 kbit/s
└── sv/
    ├── originals/  *.wav
    └── *.webm
```

The pristine espeak WAVs are kept under `<lang>/originals/` so the WebMs can be regenerated losslessly with different codec settings.

**Regenerating recordings** (regenerate the whole alphabet at once so the voice stays consistent):

```bash
# Swedish (29 letters: A–Z + Å, Ä, Ö)
LETTERS=(A B C D E F G H I J K L M N O P Q R S T U V W X Y Z Å Ä Ö)
SLUGS=(a b c d e f g h i j k l m n o p q r s t u v w x y z aa ae oe)
for i in "${!LETTERS[@]}"; do
    espeak -v sv+f3 -s 130 -p 60 \
        -w "sound/sv/originals/${SLUGS[$i]}.wav" "${LETTERS[$i]}"
done

# English (26 letters)
for L in A B C D E F G H I J K L M N O P Q R S T U V W X Y Z; do
    l=$(echo "$L" | tr A-Z a-z)
    espeak -v en-us+f3 -s 130 -p 60 -w "sound/en/originals/${l}.wav" "$L"
done
```

espeak flags: `+f3` female variant, `-s 130` slower than default for clarity, `-p 60` slightly higher pitch. Adjust and rerun the whole set.

**Re-encoding WAVs to WebM**:

```bash
for f in sound/<lang>/originals/*.wav; do
    out="sound/<lang>/$(basename "${f%.wav}").webm"
    ffmpeg -y -i "$f" -c:a libopus -b:a 32k -vbr on -application voip "$out"
done
```

If you change the audio container/extension, also update `new Audio("…/.webm")` in [script.js](script.js) and the glob in [android/build.sh](android/build.sh).

## Web architecture in one minute

- [index.html](index.html) — a near-empty body with `<div id="keyboard"></div>`. jQuery + [script.js](script.js) are loaded from local paths only. `<html lang="sv">` matches the default `LANG`.
- [script.js](script.js) — on DOM ready it:
  1. Reads `LANG`, looks up its `ALPHABETS` entry.
  2. Builds `.row > .key` markup based on `letters` + `rows`; the `data-letter` attribute is the contract between HTML, CSS (per-key colors), JS (sound lookup), and the filesystem (via `slugs`).
  3. Pre-creates an `Audio` per key pointing at `sound/<LANG>/<slug>.webm` and preloads them.
  4. Wires two input paths to the same `playLetter` + `flash` pair:
     - `pointerdown` on `.key` (single handler for mouse, touch, pen — fires immediately on finger-down).
     - `keydown` on `document` for physical letter keys, matching via `data-letter` so the press animation also fires.
  5. `audio.currentTime = 0` before `play()` so rapid repeat taps always restart from the beginning.
- [style.css](style.css) — flex layout (`#keyboard` column → `.row` rows → flex-1 keys), `vmin`-based sizing, per-letter colors, and a `.pressed` class for the press-down animation. `touch-action: manipulation` + `user-select: none` keep taps snappy and free of accidental selection or double-tap-zoom.

## Android app

[android/](android/) wraps the web app in a single-Activity full-screen WebView, packaged as a self-contained APK with all assets (HTML, CSS, JS, vendored jQuery, both languages of audio) bundled. No network at runtime. App label is "ABC app" (see [android/res/values/strings.xml](android/res/values/strings.xml)), package `com.example.alphabetlearner`, landscape-locked via `sensorLandscape`.

**Build, install, and launch on a connected device:**

```bash
./android/build.sh run        # build → adb install → adb launch
./android/build.sh install    # build → adb install
./android/build.sh            # build only; APK at android/build/alphabet-learner.apk
```

The build script drives the Android SDK tools directly (`aapt2`, `d8`, `apksigner`, `zipalign`) and **does not require Gradle or the Android Gradle Plugin**. Keep it that way unless the app grows past a single Activity or needs androidx — that's when Gradle starts paying for itself.

First build generates `android/debug.keystore` (gitignored). Keep that file on the machine you build from — if it gets deleted, the next build creates a new one and you'll have to uninstall before reinstalling (signature mismatch).

Defaults assume `ANDROID_HOME=/home/ekirprivat/android-sdk`, build-tools 36.0.0, platform android-36. Override via env vars at the top of [android/build.sh](android/build.sh).

When multiple devices/emulators are attached, the script's bare `adb install`/`adb start` will fail. Use `adb -s <serial>` directly, e.g. `adb -s emulator-5554 install -r android/build/alphabet-learner.apk`.

### Android architecture

- [android/AndroidManifest.xml](android/AndroidManifest.xml) — package `com.example.alphabetlearner`, single launcher Activity, `screenOrientation="sensorLandscape"`, no permissions (audio is local, no network). `configChanges` covers everything that could otherwise destroy and recreate the WebView (orientation, keyboard, density…).
- [android/src/com/example/alphabetlearner/MainActivity.java](android/src/com/example/alphabetlearner/MainActivity.java) — creates a WebView, enables JS + DOM storage, calls `setMediaPlaybackRequiresUserGesture(false)` (essential: otherwise the first tap on each letter wouldn't play sound), disables long-press / scroll bounce / zoom, loads `file:///android_asset/index.html`, and re-applies immersive sticky fullscreen on every focus gain.
- [android/res/](android/res/) — `strings.xml` (app label "ABC app"), `colors.xml`, fullscreen `AppTheme` (no action bar, transparent status/nav bars), and an adaptive launcher icon (white "A" on the app's blue) defined entirely in XML.
- [android/build.sh](android/build.sh) — pipeline: copy `index.html`/`style.css`/`script.js`/`vendor/*.js` + each `sound/<lang>/*.webm` into `assets/` → `aapt2 compile` → `aapt2 link` → `javac` → `d8` → zip `classes.dex` into the APK → `zipalign` → `apksigner sign`. Output: `android/build/alphabet-learner.apk`.

### Touch handling (the primary input path)

Three layers cooperate to make taps feel instant on the tablet:

1. **CSS** ([style.css](style.css)) — `touch-action: manipulation` disables double-tap-zoom (and its legacy 300 ms delay); `user-select: none` and `-webkit-tap-highlight-color: transparent` keep finger drags from selecting text or flashing the system highlight; the press animation is driven by a `.pressed` class added in JS, not by `:active`, so it works identically on mouse and touch.
2. **JS** ([script.js](script.js)) — `pointerdown` (not `click`) so the sound fires on finger-down with no waiting period.
3. **WebView** ([android/src/com/example/alphabetlearner/MainActivity.java](android/src/com/example/alphabetlearner/MainActivity.java)) — disables long-click, haptics, scroll bars, and over-scroll glow so nothing in the host competes with the page's tap handling; `setMediaPlaybackRequiresUserGesture(false)` lets `Audio.play()` succeed from those pointerdowns without WebView gating.

**If "touches don't do anything" ever returns, suspect that jQuery didn't load before suspecting touch wiring.** All handlers live inside `$(function(){…})`; a missing `$` makes every key inert with no visual feedback at all — same symptom as a broken touch path.

## Workflow

The product spec asks for a commit after each change and to start the app to try it out. Follow that: small, focused commits, and serve the directory locally (or rebuild and `adb install` the APK) to verify visually/audibly before reporting work done.

When the user is away from the computer and the next step blocks on them (try the app, answer a question), call out with `espeak` — they may not be looking at the terminal.
