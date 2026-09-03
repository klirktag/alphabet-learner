#!/usr/bin/env bash
# Build a flatpak bundle of the desktop app.
#
# One-time prerequisites (system-level, not scripted here on purpose):
#   flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
#   flatpak install --user flathub org.freedesktop.Platform//24.08 \
#       org.freedesktop.Sdk//24.08 org.electronjs.Electron2.BaseApp//24.08
#
# Usage: ./build.sh   (from anywhere)
set -euo pipefail

# A terminal opened inside VS Code's snap can leak XDG_DATA_HOME/XDG_DATA_DIRS
# pointing at the snap's own private data dir, silently redirecting flatpak
# installs/builds into ~/snap/code/<rev>/.local/share/flatpak instead of the
# real ~/.local/share/flatpak. Force the real defaults.
unset XDG_DATA_HOME XDG_DATA_DIRS

FLATPAK_DIR="$(cd "$(dirname "$0")" && pwd)"
DESKTOP_DIR="$(cd "$FLATPAK_DIR/.." && pwd)"

cd "$DESKTOP_DIR"
bash build-assets.sh
npx electron-builder --config flatpak/electron-builder.yml --linux flatpak

BUNDLE=$(ls -t "$FLATPAK_DIR"/dist/*.flatpak 2>/dev/null | head -1)
echo
if [ -n "${BUNDLE:-}" ]; then
    echo "Built: $BUNDLE"
    echo "Install with: flatpak/install.sh"
else
    echo "Build finished but no .flatpak bundle found in flatpak/dist/ — check output above." >&2
    exit 1
fi
