#!/usr/bin/env bash
# Install the most recently built flatpak bundle for the current user.
set -euo pipefail

# See build.sh — avoid a VS Code snap terminal silently redirecting this to
# the wrong flatpak installation.
unset XDG_DATA_HOME XDG_DATA_DIRS

FLATPAK_DIR="$(cd "$(dirname "$0")" && pwd)"
BUNDLE=$(ls -t "$FLATPAK_DIR"/dist/*.flatpak 2>/dev/null | head -1)
[ -n "${BUNDLE:-}" ] || { echo "No .flatpak bundle found — run flatpak/build.sh first." >&2; exit 1; }

flatpak install --user --bundle -y "$BUNDLE"
echo "Installed. Launch with: flatpak run se.ekirprivat.abcapp"
