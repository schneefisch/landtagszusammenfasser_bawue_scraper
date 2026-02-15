#!/usr/bin/env bash
# One-time setup: clones the upstream landtagszusammenfasser repo with submodules.
# Idempotent — skips if already cloned.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CLONE_DIR="$PROJECT_ROOT/docker/landtagszusammenfasser"

if [ -d "$CLONE_DIR/.git" ]; then
    echo "Upstream repo already cloned at $CLONE_DIR"
    echo "Updating submodules..."
    git -C "$CLONE_DIR" submodule update --init --recursive
    echo "Done."
    exit 0
fi

echo "Cloning Chrystalkey/landtagszusammenfasser into $CLONE_DIR..."
mkdir -p "$PROJECT_ROOT/docker"
git clone --recurse-submodules https://github.com/Chrystalkey/landtagszusammenfasser.git "$CLONE_DIR"
echo "Clone complete."
