# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A single-page web app that teaches kids the alphabet — built first for the project owner's Swedish-speaking child. The whole screen is one big keyboard whose keys are arranged **alphabetically, not QWERTY** — this is deliberate for pedagogical reasons; do not reorder them. Tapping a key (or pressing the matching physical key) plays a recording of the letter's name from the currently selected audio source.

The same web app is also packaged as a native Android APK ([android/](android/)) that bundles every asset and runs offline in a full-screen WebView. The primary deployment target is the kid's tablet — **touch is the main interaction**, not a mouse.

## Product constraints (do not change without asking)

- **Stack: plain HTML, CSS, JavaScript + jQuery only.** No build step for the web side, no bundler, no React/Vue/etc. jQuery is **vendored** at [vendor/jquery-3.7.1.min.js](vendor/jquery-3.7.1.min.js); the page loads it from there. Do not switch back to a CDN — Android WebView pages loaded from `file://` fail to fetch CDN scripts, and the whole app dies silently because every handler lives inside `$(function(){…})`.
- **Keyboard order is alphabetical**, with rows defined per-language in [script.js](script.js) (Swedish: 7/8/7/7, English: 6/7/7/6). Keep it that way.
- **Keys fill the viewport.** Sizing uses `vmin` units in [style.css](style.css) so the keyboard scales to phones, tablets, and desktop without scrolling.
- **Visual style is colorful and child-friendly** (rounded keys, bright per-letter colors, playful font). Per-key colors are assigned via `.key[data-letter="x"]` selectors, cycling through ~9 hues. Å, Ä, Ö continue the cycle.
- **One sound per letter**, served from [sound/](sound/) as Opus-in-WebM (~4 KB each). Audio objects are pre-created on source-switch so playback is instant.
- **Touch is the primary input.** Click/mouse and physical-keyboard support are nice extras but the design target is finger taps on a tablet.

## Language and audio-source configuration

There are two orthogonal axes:

1. **Language** (`LANG` constant in [script.js](script.js)) — which alphabet to display. Code-only for now; a settings UI will replace this later.
2. **Source** (chosen via the **Settings popup**, opened with the cog wheel ⚙ in the bottom-right corner) — which recording set the keys play from. The popup is dismissed with its `×` button, by tapping the dark backdrop, or by pressing Esc on desktop. The choice persists to `localStorage` and survives reload.

`ALPHABETS[LANG]` defines the alphabet, row layout, and unicode→ASCII slug mapping for filename-safe lookup (`å→aa`, `ä→ae`, `ö→oe`).

`SOURCES[LANG]` is an ordered list of `{ id, label }` entries. The chip cycles through them in order; each entry resolves to `sound/<LANG>-<id>/<slug>.webm`. **Adding a new source = drop a folder under `sound/` and append one line to `SOURCES[LANG]`** — that's the whole contract.

## Audio sources currently shipped

```
sound/
├── en-espeak/        26 letters · espeak en-us+f3                       (synthetic)
├── sv-espeak/        29 letters · espeak sv+f3                          (synthetic)
├── sv-piper-nst/     29 letters · Piper, NST corpus, sounds male        (neural)
├── sv-piper-alma/    29 letters · Piper, alma voice, female             (neural)
├── sv-piper-lisa/    29 letters · Piper, lisa voice, female             (neural)
└── sv-recorded/      29 letters · placeholder = sv-espeak (overwrite!)  (room for human recordings)
```

Each `<source>/` folder holds `*.webm` (encoded for app use) plus `originals/*.wav` (lossless source so the WebMs can be re-encoded later).

## Licenses of bundled audio sources

| Source | Engine license | Voice / data license | Redistribute? |
| --- | --- | --- | --- |
| `*-espeak` | espeak-ng GPL-3 (engine) | n/a — output of a synth not treated as derivative | Yes, freely |
| `sv-piper-nst` | Piper MIT | NST corpus & model CC0 | Yes, no attribution required (a credit line is polite) |
| `sv-piper-alma` | Piper MIT | Model **CC BY 4.0** | Yes, **attribution required** in distributed app |
| `sv-piper-lisa` | Piper MIT | Model license not stated in upstream model card | **Verify before distributing** outside personal use |
| `sv-recorded` | n/a | Owned by whoever records (initially espeak placeholders) | Owner's call |

Suggested attribution line for an About / credits screen:

> Swedish voices: Piper TTS (MIT). Voice "nst" trained by KBLab at the National Library of Sweden on the NST Swedish speech corpus (CC0). Voice "alma" by yeagersthlm (CC BY 4.0).

## Run the web version

No build, no dependencies. Just serve the directory:

```bash
python3 -m http.server 8000
# then open http://localhost:8000
```

Browser compatibility: Firefox, Chrome/Chromium, Brave, and Android WebView all play Opus-in-WebM. Safari does not, but Safari isn't a target. **Do not switch the audio container back to MP4** — Firefox refuses to play Opus-in-MP4 (codec OK, container not). That bit us before.

## Regenerating audio

### espeak

```bash
# Swedish (29 letters: A–Z + Å, Ä, Ö)
LETTERS=(A B C D E F G H I J K L M N O P Q R S T U V W X Y Z Å Ä Ö)
SLUGS=(a b c d e f g h i j k l m n o p q r s t u v w x y z aa ae oe)
for i in "${!LETTERS[@]}"; do
    espeak -v sv+f3 -s 130 -p 60 \
        -w "sound/sv-espeak/originals/${SLUGS[$i]}.wav" "${LETTERS[$i]}"
done

# English (26 letters): swap -v sv+f3 → -v en-us+f3, iterate A–Z, write to sound/en-espeak/originals/.
```

### Piper (installed at `~/.local/piper/`)

The Piper binary lives at `~/.local/piper/piper/piper`; the three Swedish voice files are `~/.local/piper/sv_SE-{nst,alma,lisa}-medium.onnx` (plus `.onnx.json` companions). To install fresh on another machine:

```bash
mkdir -p ~/.local/piper && cd ~/.local/piper
# Engine
curl -sSL -o piper.tar.gz https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_linux_x86_64.tar.gz
tar xzf piper.tar.gz && rm piper.tar.gz
# Each voice (~61 MB)
for v in nst alma lisa; do
    curl -sSL -o "sv_SE-${v}-medium.onnx" \
        "https://huggingface.co/rhasspy/piper-voices/resolve/main/sv/sv_SE/${v}/medium/sv_SE-${v}-medium.onnx"
    curl -sSL -o "sv_SE-${v}-medium.onnx.json" \
        "https://huggingface.co/rhasspy/piper-voices/resolve/main/sv/sv_SE/${v}/medium/sv_SE-${v}-medium.onnx.json"
done
```

Generating all 29 letters for one Piper voice:

```bash
PIPER=~/.local/piper/piper/piper
for i in "${!LETTERS[@]}"; do
    echo "${LETTERS[$i]}" | $PIPER \
        --model "~/.local/piper/sv_SE-nst-medium.onnx" \
        --output_file "sound/sv-piper-nst/originals/${SLUGS[$i]}.wav"
done
```

### Encoding any WAV to the served WebM

```bash
for f in sound/<source>/originals/*.wav; do
    out="sound/<source>/$(basename "${f%.wav}").webm"
    ffmpeg -y -i "$f" -c:a libopus -b:a 32k -vbr on -application voip "$out"
done
```

If you change the audio extension, also update `new Audio("…/.webm")` in [script.js](script.js) and the glob in [android/build.sh](android/build.sh).

### Optional: mbrola as a 4th Swedish source

`/home/ekirprivat/install-tools.sh` queues the system packages (`mbrola mbrola-sw1 mbrola-sw2`) for an mbrola-voiced espeak. Modest quality bump over plain espeak; install with `sudo bash /home/ekirprivat/install-tools.sh`, then regenerate with `espeak -v mb-sw1 …` into a new `sound/sv-espeak-mbrola/` folder and add the matching `SOURCES.sv` entry.

## Web architecture in one minute

- [index.html](index.html) — a near-empty body with `<div id="keyboard"></div>` plus local jQuery + [script.js](script.js). `<html lang="sv">` matches the default `LANG`.
- [script.js](script.js) — on DOM ready it:
  1. Reads `LANG`, looks up `ALPHABETS[LANG]` and `SOURCES[LANG]`.
  2. Reads `localStorage["abc-app:source:" + LANG]` to recall the last source picked.
  3. Builds `.row > .key` markup based on `letters` + `rows`; the `data-letter` attribute is the contract between HTML, CSS (per-key colors), JS (sound lookup), and the filesystem (via `slugs`).
  4. Inside `loadSounds()`: pre-creates an `Audio` per key pointing at `sound/<LANG>-<source.id>/<slug>.webm` and preloads them. Called again whenever the chip switches source.
  5. Renders the floating cog (`#settings-cog`) in the bottom-right corner.
  6. Builds the hidden `#settings-overlay` modal containing the **Settings** card with a `×` close button and the audio-source row (current name + Switch audio button). Cog opens it; `×`, backdrop tap, or Esc closes it.
  7. Wires the keyboard's `pointerdown` and `document.keydown` (physical A–Z + ÅÄÖ) to `playLetter` + `flash`. `audio.currentTime = 0` before `play()` so rapid repeat taps always restart from the beginning.
- [style.css](style.css) — flex layout (`#keyboard` column → `.row` rows → flex-1 keys), `vmin`-based sizing, per-letter colors, a `.pressed` press-down animation, the floating `#settings-cog`, and the modal `#settings-overlay` + `.settings-card`. `touch-action: manipulation` + `user-select: none` keep taps snappy.

## Android app

[android/](android/) wraps the web app in a single-Activity full-screen WebView, packaged as a self-contained APK with all assets (HTML, CSS, JS, vendored jQuery, every `sound/<lang>-<source>/` folder) bundled. No network at runtime. App label is **"ABC app"** ([android/res/values/strings.xml](android/res/values/strings.xml)), package `com.example.alphabetlearner`, landscape-locked via `sensorLandscape`.

**Build, install, and launch on a connected device:**

```bash
./android/build.sh run        # build → adb install → adb launch
./android/build.sh install    # build → adb install
./android/build.sh            # build only; APK at android/build/alphabet-learner.apk
```

The build script drives the Android SDK tools directly (`aapt2`, `d8`, `apksigner`, `zipalign`) and **does not require Gradle or the Android Gradle Plugin**. Keep it that way unless the app grows past a single Activity or needs androidx.

First build generates `android/debug.keystore` (gitignored). Keep that file on the machine you build from — if it gets deleted, the next build creates a new one and you'll have to uninstall before reinstalling (signature mismatch).

Defaults assume `ANDROID_HOME=/home/ekirprivat/android-sdk`, build-tools 36.0.0, platform android-36.

**Multiple devices/emulators**: `adb install`/`adb start` without `-s` fails when more than one device is attached. Pass `adb -s <serial>` (use `adb devices -l` to list them) — the tablet's serial is `HA22VWLS`.

### Android architecture

- [android/AndroidManifest.xml](android/AndroidManifest.xml) — package `com.example.alphabetlearner`, single launcher Activity, `screenOrientation="sensorLandscape"`, no permissions. `configChanges` covers everything that could otherwise destroy and recreate the WebView (orientation, keyboard, density…).
- [android/src/com/example/alphabetlearner/MainActivity.java](android/src/com/example/alphabetlearner/MainActivity.java) — creates a WebView, enables JS + DOM storage, calls `setMediaPlaybackRequiresUserGesture(false)` (essential: otherwise the first tap on each letter wouldn't play sound), disables long-press / scroll bounce / zoom, loads `file:///android_asset/index.html`, and re-applies immersive sticky fullscreen on every focus gain.
- [android/res/](android/res/) — `strings.xml`, `colors.xml`, fullscreen `AppTheme`, and an adaptive launcher icon (white "A" on the app's blue) defined entirely in XML.
- [android/build.sh](android/build.sh) — pipeline: copy `index.html`/`style.css`/`script.js`/`vendor/*.js` + every `sound/*/*.webm` into `assets/` → `aapt2 compile` → `aapt2 link` → `javac` → `d8` → zip `classes.dex` into the APK → `zipalign` → `apksigner sign`. Output: `android/build/alphabet-learner.apk`.

### Touch handling (the primary input path)

Three layers cooperate to make taps feel instant on the tablet:

1. **CSS** ([style.css](style.css)) — `touch-action: manipulation` disables double-tap-zoom (and its legacy 300 ms delay); `user-select: none` and `-webkit-tap-highlight-color: transparent` keep finger drags from selecting text or flashing the system highlight; the press animation is driven by a `.pressed` class added in JS, not by `:active`, so it works identically on mouse and touch.
2. **JS** ([script.js](script.js)) — `pointerdown` (not `click`) so the sound fires on finger-down with no waiting period.
3. **WebView** ([android/src/com/example/alphabetlearner/MainActivity.java](android/src/com/example/alphabetlearner/MainActivity.java)) — disables long-click, haptics, scroll bars, and over-scroll glow so nothing in the host competes with the page's tap handling; `setMediaPlaybackRequiresUserGesture(false)` lets `Audio.play()` succeed from those pointerdowns without WebView gating.

**If "touches don't do anything" ever returns, suspect that jQuery didn't load before suspecting touch wiring.** All handlers live inside `$(function(){…})`; a missing `$` makes every key inert with no visual feedback at all — same symptom as a broken touch path.

## Workflow

Small, focused commits, and serve the directory locally (or rebuild and `adb install` the APK) to verify visually/audibly before reporting work done.

When the user is away from the computer and the next step blocks on them (try the app, answer a question), call out with `espeak` — they may not be looking at the terminal.
