#!/usr/bin/env bash
# Stop the LTZF test backend.
# Usage:
#   ./scripts/stop.sh        — stop containers (data preserved)
#   ./scripts/stop.sh -v     — stop containers AND wipe database volume
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
COMPOSE_DIR="$SCRIPT_DIR/../docker/landtagszusammenfasser"

if [ ! -f "$COMPOSE_DIR/docker-compose.yml" ]; then
    echo "Error: Upstream repo not found. Nothing to stop."
    exit 1
fi

if [ "${1:-}" = "-v" ]; then
    echo "Stopping LTZF test backend and removing volumes..."
    docker-compose -f "$COMPOSE_DIR/docker-compose.yml" down -v
    echo "Stopped. Database volume removed."
else
    echo "Stopping LTZF test backend..."
    docker-compose -f "$COMPOSE_DIR/docker-compose.yml" down
    echo "Stopped. Database volume preserved (use -v to wipe)."
fi
