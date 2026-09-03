#!/usr/bin/env bash
# Copy the web app into desktop/app/ so it can run standalone (no HTTP
# server) and be packaged by electron-builder. Mirrors android/build.sh:
# ships every audio-packs/<lang>-<source>/*.webm plus word audio/images,
# skips originals/*.wav (dev-only source material).
set -euo pipefail

DESKTOP_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$DESKTOP_DIR/.." && pwd)"
APP="$DESKTOP_DIR/app"

echo ">> Cleaning $APP"
rm -rf "$APP"
mkdir -p "$APP/vendor" "$APP/audio-packs"

echo ">> Bundling web assets (html/css/js + vendored jQuery + per-pack audio + words)"
cp "$ROOT/index.html" "$ROOT/style.css" "$ROOT/script.js" "$APP/"
cp "$ROOT/vendor/"*.js "$APP/vendor/"

for src_dir in "$ROOT/audio-packs/"*/; do
    src=$(basename "$src_dir")
    mkdir -p "$APP/audio-packs/$src"
    cp "$src_dir"*.webm "$APP/audio-packs/$src/" 2>/dev/null || true
    if [ -d "$src_dir/words" ]; then
        for word_dir in "$src_dir/words/"*/; do
            word=$(basename "$word_dir")
            mkdir -p "$APP/audio-packs/$src/words/$word"
            find "$word_dir" -maxdepth 1 -type f -exec cp {} "$APP/audio-packs/$src/words/$word/" \;
        done
    fi
done

echo "Bundled web assets into $APP"
