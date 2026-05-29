#!/usr/bin/env bash
# Build (and optionally install/run) the Alphabet Learner Android APK.
#
# Usage:
#   ./build.sh              build android/build/alphabet-learner.apk
#   ./build.sh install      build + adb install on attached device
#   ./build.sh run          build + install + launch the activity
#
# No Gradle / no Android Gradle Plugin: drives the SDK's aapt2/d8/apksigner
# directly, which is enough for this single-Activity WebView wrapper.

set -euo pipefail

ANDROID_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$ANDROID_DIR/.." && pwd)"
BUILD="$ANDROID_DIR/build"

SDK="${ANDROID_HOME:-/home/ekirprivat/android-sdk}"
BUILD_TOOLS_VER="${BUILD_TOOLS_VER:-36.0.0}"
PLATFORM_VER="${PLATFORM_VER:-36}"
MIN_SDK="${MIN_SDK:-24}"
TARGET_SDK="${TARGET_SDK:-36}"
PKG="com.example.alphabetlearner"

BT="$SDK/build-tools/$BUILD_TOOLS_VER"
PLATFORM_JAR="$SDK/platforms/android-$PLATFORM_VER/android.jar"
ADB="$SDK/platform-tools/adb"

for f in "$BT/aapt2" "$BT/d8" "$BT/apksigner" "$BT/zipalign" "$PLATFORM_JAR"; do
    [ -e "$f" ] || { echo "Missing $f — check SDK/build-tools/platform versions." >&2; exit 1; }
done

echo ">> Cleaning $BUILD"
rm -rf "$BUILD"
mkdir -p "$BUILD"/{assets/sound,classes,dex,gen}

echo ">> Bundling web assets (html/css/js + vendored jQuery + per-source sounds + words)"
cp "$ROOT/index.html" "$ROOT/style.css" "$ROOT/script.js" "$BUILD/assets/"
mkdir -p "$BUILD/assets/vendor"
cp "$ROOT/vendor/"*.js "$BUILD/assets/vendor/"
# Ship every sound/<lang>-<source>/ folder. Skip wav originals + READMEs.
for src_dir in "$ROOT/sound/"*/; do
    src=$(basename "$src_dir")
    mkdir -p "$BUILD/assets/sound/$src"
    cp "$src_dir"*.webm "$BUILD/assets/sound/$src/"
    # Per-word folders (Visa ord feature): copy audio.webm + image.* per word,
    # skip the originals/ subdir.
    if [ -d "$src_dir/words" ]; then
        for word_dir in "$src_dir/words/"*/; do
            word=$(basename "$word_dir")
            mkdir -p "$BUILD/assets/sound/$src/words/$word"
            find "$word_dir" -maxdepth 1 -type f -exec cp {} "$BUILD/assets/sound/$src/words/$word/" \;
        done
    fi
done

echo ">> aapt2 compile (resources)"
"$BT/aapt2" compile --dir "$ANDROID_DIR/res" -o "$BUILD/res.zip"

echo ">> aapt2 link (manifest + resources + assets -> unsigned APK)"
"$BT/aapt2" link \
    --min-sdk-version "$MIN_SDK" \
    --target-sdk-version "$TARGET_SDK" \
    -I "$PLATFORM_JAR" \
    --manifest "$ANDROID_DIR/AndroidManifest.xml" \
    -A "$BUILD/assets" \
    --java "$BUILD/gen" \
    -o "$BUILD/app-unsigned.apk" \
    "$BUILD/res.zip"

echo ">> javac (app + generated R)"
find "$ANDROID_DIR/src" "$BUILD/gen" -name '*.java' > "$BUILD/sources.txt"
javac \
    -d "$BUILD/classes" \
    -classpath "$PLATFORM_JAR" \
    -source 8 -target 8 \
    -Xlint:-options \
    @"$BUILD/sources.txt"

echo ">> d8 (classes -> classes.dex)"
mapfile -t CLASSES < <(find "$BUILD/classes" -name '*.class')
"$BT/d8" --min-api "$MIN_SDK" --output "$BUILD/dex" "${CLASSES[@]}"

echo ">> bundling classes.dex into APK"
cp "$BUILD/app-unsigned.apk" "$BUILD/app-with-dex.apk"
( cd "$BUILD/dex" && zip -q "$BUILD/app-with-dex.apk" classes.dex )

KEYSTORE="$ANDROID_DIR/debug.keystore"
if [ ! -f "$KEYSTORE" ]; then
    echo ">> generating debug keystore ($KEYSTORE)"
    keytool -genkeypair \
        -keystore "$KEYSTORE" \
        -storepass android -keypass android \
        -alias androiddebugkey \
        -dname "CN=Android Debug,O=Android,C=US" \
        -keyalg RSA -keysize 2048 -validity 10000
fi

echo ">> zipalign"
"$BT/zipalign" -p -f 4 "$BUILD/app-with-dex.apk" "$BUILD/app-aligned.apk"

echo ">> apksigner sign"
"$BT/apksigner" sign \
    --ks "$KEYSTORE" \
    --ks-pass pass:android \
    --key-pass pass:android \
    --min-sdk-version "$MIN_SDK" \
    --out "$BUILD/alphabet-learner.apk" \
    "$BUILD/app-aligned.apk"

"$BT/apksigner" verify "$BUILD/alphabet-learner.apk" && echo "Signature OK"

APK="$BUILD/alphabet-learner.apk"
echo
echo "Built: $APK ($(du -h "$APK" | cut -f1))"

case "${1:-}" in
    install)
        "$ADB" install -r "$APK"
        ;;
    run)
        "$ADB" install -r "$APK"
        "$ADB" shell am start -n "$PKG/$PKG.MainActivity"
        ;;
esac
