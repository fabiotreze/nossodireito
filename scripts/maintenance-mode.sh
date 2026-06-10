#!/bin/bash
set -euo pipefail

# maintenance-mode.sh — Toggle emergency maintenance mode without portal.
# Usage: ./scripts/maintenance-mode.sh on|off [timeout-seconds]
# Example: ./scripts/maintenance-mode.sh on 600

ACTION="${1:-}"
TIMEOUT="${2:-300}"
RESOURCE_GROUP="rg-nossodireito-br"
APP_SERVICE="app-nossodireito-br"

if [[ -z "$ACTION" ]]; then
  echo "Usage: $0 on|off [timeout-seconds]"
  echo "  on     — enable maintenance mode (returns 503)"
  echo "  off    — disable maintenance mode"
  echo "  timeout-seconds — retry-after header value (default 300)"
  exit 1
fi

if [[ "$ACTION" != "on" && "$ACTION" != "off" ]]; then
  echo "Error: ACTION must be 'on' or 'off'"
  exit 1
fi

# Ensure az CLI is authenticated
if ! az account show >/dev/null 2>&1; then
  echo "Error: Not authenticated. Run 'az login' first."
  exit 1
fi

echo "[maintenance-mode] Connecting to App Service $APP_SERVICE in $RESOURCE_GROUP..."

if [[ "$ACTION" == "on" ]]; then
  echo "[maintenance-mode] Enabling maintenance mode (MAINTENANCE_MODE=true, MAINTENANCE_RETRY_AFTER=$TIMEOUT)..."
  az webapp config appsettings set \
    --resource-group "$RESOURCE_GROUP" \
    --name "$APP_SERVICE" \
    --settings "MAINTENANCE_MODE=true" "MAINTENANCE_RETRY_AFTER=$TIMEOUT" \
    >/dev/null
  echo "[maintenance-mode] ✓ Maintenance mode ON"
  echo "[maintenance-mode] Public routes now return 503. Health check remains available."
  echo "[maintenance-mode] Retry-After: $TIMEOUT seconds"
elif [[ "$ACTION" == "off" ]]; then
  echo "[maintenance-mode] Disabling maintenance mode (MAINTENANCE_MODE=false)..."
  az webapp config appsettings set \
    --resource-group "$RESOURCE_GROUP" \
    --name "$APP_SERVICE" \
    --settings "MAINTENANCE_MODE=false" \
    >/dev/null
  echo "[maintenance-mode] ✓ Maintenance mode OFF"
  echo "[maintenance-mode] Public service restored."
fi

# Verify
echo "[maintenance-mode] Verifying state..."
CURRENT=$(az webapp config appsettings list \
  --resource-group "$RESOURCE_GROUP" \
  --name "$APP_SERVICE" \
  --query "[?name=='MAINTENANCE_MODE'].value" -o tsv)

echo "[maintenance-mode] Current MAINTENANCE_MODE: $CURRENT"
