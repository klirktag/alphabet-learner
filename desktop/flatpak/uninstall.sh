#!/usr/bin/env bash
set -euo pipefail

# See build.sh — avoid a VS Code snap terminal silently redirecting this to
# the wrong flatpak installation.
unset XDG_DATA_HOME XDG_DATA_DIRS

flatpak uninstall --user -y se.ekirprivat.abcapp
