#!/usr/bin/env bash
# Verify the LTZF test backend is running and bootstrap a collector API key.
# - Waits for the API at localhost:8080
# - Calls GET /ping health check
# - Creates a collector API key using the keyadder bootstrap key
# - Tests PUT /api/v2/vorgang with a sample BW legislative proceeding
# - Prints the collector API key for use in scraper development
set -euo pipefail

API_URL="${LTZF_API_URL:-http://localhost:8080}"
KEYADDER_KEY="${LTZF_KEYADDER_KEY:-tegernsee-apfelsaft-co2grenzwert}"

echo "=== LTZF Test Backend Verification ==="
echo ""

# 1. Wait for API
echo "[1/4] Waiting for API at $API_URL..."
MAX_WAIT=120
WAITED=0
while ! curl -sf "$API_URL/ping" > /dev/null 2>&1; do
    if [ "$WAITED" -ge "$MAX_WAIT" ]; then
        echo "FAIL: API not available after ${MAX_WAIT}s. Is the backend running?"
        echo "  Run: ./scripts/start.sh"
        exit 1
    fi
    sleep 2
    WAITED=$((WAITED + 2))
done
echo "  OK — API responding at $API_URL"

# 2. Health check
echo ""
echo "[2/4] Health check (GET /ping)..."
PING_RESPONSE=$(curl -sf "$API_URL/ping" 2>&1) || true
echo "  Response: $PING_RESPONSE"
echo "  OK"

# 3. Create collector API key
echo ""
echo "[3/4] Creating collector API key (POST /api/v2/auth)..."
COLLECTOR_KEY=$(curl -sf -X POST "$API_URL/api/v2/auth" \
    -H "Content-Type: application/json" \
    -H "X-API-Key: $KEYADDER_KEY" \
    -d '{"scope": "collector"}')

if [ -z "$COLLECTOR_KEY" ]; then
    echo "  FAIL: Could not create collector API key."
    echo "  Check that LTZF_KEYADDER_KEY is correct (current: $KEYADDER_KEY)"
    exit 1
fi
echo "  OK — Collector API key created"

# 4. Test PUT /api/v2/vorgang with sample data
echo ""
echo "[4/4] Testing PUT /api/v2/vorgang with sample BW proceeding..."
SCRAPER_ID="$(python3 -c 'import uuid; print(uuid.uuid4())')"
VORGANG_ID="$(python3 -c 'import uuid; print(uuid.uuid4())')"

HTTP_CODE=$(curl -sf -o /dev/null -w "%{http_code}" -X PUT "$API_URL/api/v2/vorgang" \
    -H "Content-Type: application/json" \
    -H "X-API-Key: $COLLECTOR_KEY" \
    -H "X-Scraper-Id: $SCRAPER_ID" \
    -d "$(cat <<PAYLOAD
{
    "api_id": "$VORGANG_ID",
    "titel": "Gesetz zur Änderung des Landesnaturschutzgesetzes",
    "kurztitel": "Naturschutzgesetz-Novelle BW",
    "wahlperiode": 17,
    "verfassungsaendernd": false,
    "typ": "gg-land-parl",
    "initiatoren": [
        {"organisation": "Fraktion GRÜNE", "person": "Dr. Andre Baumann"}
    ],
    "stationen": [
        {
            "typ": "parl-initiativ",
            "zp_start": "2026-01-15T10:00:00+01:00",
            "gremium": {
                "parlament": "BW",
                "name": "plenum",
                "wahlperiode": 17
            },
            "dokumente": []
        }
    ]
}
PAYLOAD
)")

if [ "$HTTP_CODE" = "201" ]; then
    echo "  OK — PUT returned 201 Created (Vorgang ID: $VORGANG_ID)"
elif [ "$HTTP_CODE" = "304" ]; then
    echo "  OK — PUT returned 304 Not Modified (already exists)"
else
    echo "  WARN — PUT returned HTTP $HTTP_CODE (expected 201 or 304)"
fi

# Summary
echo ""
echo "==========================================="
echo "  Verification complete!"
echo ""
echo "  Collector API Key:"
echo "  $COLLECTOR_KEY"
echo ""
echo "  Use in scraper:"
echo "    export LTZF_API_URL=$API_URL"
echo "    export LTZF_API_KEY=$COLLECTOR_KEY"
echo "==========================================="
