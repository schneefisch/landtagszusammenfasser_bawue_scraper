#!/usr/bin/env bash
# Start the LTZF test backend (database + API).
# Only starts the 3 services needed for scraper development.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
COMPOSE_DIR="$SCRIPT_DIR/../docker/landtagszusammenfasser"

if [ ! -f "$COMPOSE_DIR/docker-compose.yml" ]; then
    echo "Error: Upstream repo not found. Run ./scripts/setup.sh first."
    exit 1
fi

echo "Starting LTZF test backend (database, oapi-preimage, ltzf-db)..."
echo "Note: First run builds images — this may take 10-15 min on Apple Silicon."

docker-compose -f "$COMPOSE_DIR/docker-compose.yml" up -d database oapi-preimage ltzf-db

echo ""
echo "Waiting for ltzf-db API to become available on localhost:8080..."
MAX_WAIT=300
WAITED=0
while ! curl -sf http://localhost:8080/ping > /dev/null 2>&1; do
    if [ "$WAITED" -ge "$MAX_WAIT" ]; then
        echo "Error: API did not become available within ${MAX_WAIT}s."
        echo "Check logs with: docker-compose -f $COMPOSE_DIR/docker-compose.yml logs ltzf-db"
        exit 1
    fi
    sleep 5
    WAITED=$((WAITED + 5))
    printf "\r  Waited %ds / %ds..." "$WAITED" "$MAX_WAIT"
done

echo ""
echo "LTZF API is up at http://localhost:8080"
echo ""
echo "Services running:"
docker-compose -f "$COMPOSE_DIR/docker-compose.yml" ps database oapi-preimage ltzf-db
