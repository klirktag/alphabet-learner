# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A single-page web app that teaches kids the alphabet. The whole screen is one big keyboard whose keys are arranged **alphabetically (A–Z), not QWERTY** — this is deliberate for pedagogical reasons; do not reorder them. Tapping/clicking a key, or pressing the corresponding physical key, plays a recording of that letter's name.

## Product constraints (do not change without asking)

- **Stack: plain HTML, CSS, JavaScript + jQuery only.** No build step, no bundler, no React/Vue/etc. jQuery is loaded from a CDN in `index.html`.
- **Keyboard order is alphabetical**, laid out as 6 / 7 / 7 / 6 rows in [index.html](index.html). Keep it that way.
- **Keys fill the viewport.** Sizing uses `vmin` units in [style.css](style.css) so the keyboard scales to phones, tablets, and desktop without scrolling.
- **Visual style is colorful and child-friendly** (rounded keys, bright per-letter colors, playful font). Per-key colors are assigned via `.key[data-letter="x"]` selectors.
- **One sound per letter**, served from [sound/](sound/) as `a.wav` … `z.wav`. Audio objects are pre-created on load so playback is instant.

## Run it

No build, no dependencies to install. Just serve the directory:

```bash
python3 -m http.server 8000
# then open http://localhost:8000
```

Any static file server works (`npx serve`, etc.) — the app is fully client-side.

## Regenerating letter sounds

The sound files were generated with `espeak`. To recreate them (e.g. to change voice, speed, or pitch), run from the repo root:

```bash
for L in A B C D E F G H I J K L M N O P Q R S T U V W X Y Z; do
  l=$(echo "$L" | tr A-Z a-z)
  espeak -v en-us+f3 -s 130 -p 60 -w "sound/${l}.wav" "$L"
done
```

Flags used: `-v en-us+f3` (US English, female variant 3), `-s 130` (slower than default for clarity), `-p 60` (slightly higher pitch). Adjust and re-run for the whole set so all 26 letters stay consistent.

If a different TTS tool is used (festival, pico2wave, gTTS, recorded human voice, …), keep the same filenames (`sound/<lowercase-letter>.wav`) so [script.js](script.js) finds them — or update the extension in `new Audio("sound/" + letter + ".wav")` in [script.js](script.js).

## Architecture in one minute

Three files, no framework state:

- [index.html](index.html) — static markup. One `<button class="key" data-letter="x">` per letter, grouped into `.row` divs. The `data-letter` attribute is the contract between HTML, CSS (per-key colors), JS (sound lookup), and the filesystem (`sound/x.wav`).
- [style.css](style.css) — flex layout (`#keyboard` column → `.row` rows → flex-1 keys), `vmin`-based sizing, and per-letter background colors. A `.pressed` class provides the press-down animation.
- [script.js](script.js) — on DOM ready, builds a `sounds` map of pre-loaded `Audio` objects keyed by letter, then wires two input paths to the same `playLetter` + `flash` pair:
  1. `pointerdown` on `.key` (covers mouse, touch, pen in one handler).
  2. `keydown` on `document` for physical A–Z keys, which looks up the matching button via `data-letter` so the visual press animation also fires.

  `audio.currentTime = 0` before `play()` so rapid repeat taps always restart the sound from the beginning.

## Workflow

The product spec asks for a commit after each change and to start the app to try it out. Follow that: small, focused commits, and serve the directory locally to verify visually/audibly before reporting work done.
