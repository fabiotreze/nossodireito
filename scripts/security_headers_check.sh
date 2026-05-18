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

URLS=(
  "https://app-nossodireito-br.azurewebsites.net/"
  "https://nossodireito.fabiotreze.com/"
)

REQUIRED_HEADERS=(
  "strict-transport-security"
  "content-security-policy"
  "x-content-type-options"
  "x-frame-options"
  "referrer-policy"
  "permissions-policy"
)

EXIT_CODE=0

for url in "${URLS[@]}"; do
  echo "=== ${url} ==="
  headers="$(curl -sI "$url" | tr '[:upper:]' '[:lower:]')"
  for hdr in "${REQUIRED_HEADERS[@]}"; do
    if grep -q "^${hdr}:" <<<"$headers"; then
      echo "[OK] ${hdr}"
    else
      echo "[FAIL] Missing header: ${hdr}"
      EXIT_CODE=1
    fi
  done
  echo

done

if [[ $EXIT_CODE -eq 0 ]]; then
  echo "Security header baseline passed."
else
  echo "Security header baseline failed."
fi

exit $EXIT_CODE
