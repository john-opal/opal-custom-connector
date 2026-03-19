#!/usr/bin/env bash
# check-state.sh — Inspect live connector state
#
# Usage:
#   ./check-state.sh                          # local dev, no signing secret
#   ./check-state.sh -s <signing_secret>      # with HMAC signing
#   ./check-state.sh -u http://host:8000      # custom base URL
#   APP_ID=my-app-id ./check-state.sh         # override app_id
#
# Environment variables:
#   OPAL_SIGNING_SECRET  — signing secret (alternative to -s flag)
#   APP_ID               — app_id query param sent to the connector (default: "opal")

set -euo pipefail

BASE_URL="http://localhost:8000"
SIGNING_SECRET="${OPAL_SIGNING_SECRET:-}"
APP_ID="${APP_ID:-opal}"

usage() {
  grep '^#' "$0" | sed 's/^# \{0,1\}//'
  exit 1
}

while getopts ":u:s:h" opt; do
  case $opt in
    u) BASE_URL="$OPTARG" ;;
    s) SIGNING_SECRET="$OPTARG" ;;
    h) usage ;;
    *) echo "Unknown option: -$OPTARG" >&2; usage ;;
  esac
done

# Build the required auth headers.
# When OPAL_SIGNING_SECRET is empty the connector skips verification but
# FastAPI still requires the headers to be present.
make_headers() {
  local body="${1:-}"
  local ts
  ts=$(date +%s)

  if [[ -n "$SIGNING_SECRET" ]]; then
    local signing_string="v0:${ts}:${body}"
    local sig
    sig=$(printf '%s' "$signing_string" | openssl dgst -sha256 -hmac "$SIGNING_SECRET" -hex | awk '{print $NF}')
    echo -H "X-Opal-Request-Timestamp: ${ts}" -H "X-Opal-Signature: ${sig}"
  else
    echo -H "X-Opal-Request-Timestamp: ${ts}" -H "X-Opal-Signature: dev"
  fi
}

hr() { printf '%0.s─' $(seq 1 60); echo; }

hr
echo "Connector: $BASE_URL"
echo "App ID:    $APP_ID"
[[ -n "$SIGNING_SECRET" ]] && echo "Auth:      HMAC-SHA256" || echo "Auth:      unsigned (local dev)"
hr

echo
echo "▶ GET /users  (all provisioned users)"
hr
eval curl -sf $(make_headers) \
  "'${BASE_URL}/users?app_id=${APP_ID}'" | python3 -m json.tool

echo
echo "▶ GET /groups/app-access/users  (group members)"
hr
eval curl -sf $(make_headers) \
  "'${BASE_URL}/groups/app-access/users?app_id=${APP_ID}'" | python3 -m json.tool
