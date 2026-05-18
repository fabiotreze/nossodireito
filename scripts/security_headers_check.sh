#!/usr/bin/env bash
set -euo pipefail

# Checks critical security headers for NossoDireito endpoints.

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "[ERROR] Missing command: $1" >&2
    exit 1
  }
}

require_cmd curl

PUBLIC_URL="${PUBLIC_URL:-https://nossodireito.fabiotreze.com/}"
DIRECT_AZURE_URL="${DIRECT_AZURE_URL:-https://app-nossodireito-br.azurewebsites.net/}"
EXPECTED_DIRECT_STATUS="${EXPECTED_DIRECT_STATUS:-403}"

REQUIRED_HEADERS=(
  "strict-transport-security"
  "content-security-policy"
  "x-content-type-options"
  "x-frame-options"
  "referrer-policy"
  "permissions-policy"
)

EXIT_CODE=0

echo "=== Direct host hardening (${DIRECT_AZURE_URL}) ==="
direct_status="$(curl -s -o /dev/null -w "%{http_code}" "$DIRECT_AZURE_URL")"
if [[ "$direct_status" == "$EXPECTED_DIRECT_STATUS" ]]; then
  echo "[OK] Direct Azure host returns ${direct_status} (blocked as expected)"
else
  echo "[FAIL] Direct Azure host returned ${direct_status}; expected ${EXPECTED_DIRECT_STATUS}"
  EXIT_CODE=1
fi
echo

echo "=== Public domain headers (${PUBLIC_URL}) ==="
public_status="$(curl -s -o /dev/null -w "%{http_code}" "$PUBLIC_URL")"
if [[ "$public_status" =~ ^[23] ]]; then
  echo "[OK] Public domain reachable (${public_status})"
else
  echo "[FAIL] Public domain not reachable (${public_status})"
  EXIT_CODE=1
fi

headers="$(curl -sI "$PUBLIC_URL" | tr '[:upper:]' '[:lower:]')"
for hdr in "${REQUIRED_HEADERS[@]}"; do
  if grep -q "^${hdr}:" <<<"$headers"; then
    echo "[OK] ${hdr}"
  else
    echo "[FAIL] Missing header: ${hdr}"
    EXIT_CODE=1
  fi
done

if [[ $EXIT_CODE -eq 0 ]]; then
  echo "Security header baseline passed."
else
  echo "Security header baseline failed."
fi

exit $EXIT_CODE
