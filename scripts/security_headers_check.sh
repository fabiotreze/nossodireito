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

# Cloudflare WAF blocks default curl User-Agent from datacenter IPs (GitHub
# Actions runners). Use a normal browser UA to bypass anti-bot heuristic.
UA="${HTTP_USER_AGENT:-Mozilla/5.0 (compatible; NossoDireito-SecurityBaseline/1.0; +https://github.com/fabiotreze/nossodireito)}"
CURL_OPTS=(-sS --max-time 20 -A "$UA")

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
direct_status="$(curl "${CURL_OPTS[@]}" -o /dev/null -w "%{http_code}" "$DIRECT_AZURE_URL")"
if [[ "$direct_status" == "$EXPECTED_DIRECT_STATUS" ]]; then
  echo "[OK] Direct Azure host returns ${direct_status} (blocked as expected)"
else
  echo "[FAIL] Direct Azure host returned ${direct_status}; expected ${EXPECTED_DIRECT_STATUS}"
  EXIT_CODE=1
fi
echo

echo "=== Public domain reachability (${PUBLIC_URL}) ==="
public_status="$(curl "${CURL_OPTS[@]}" -o /dev/null -w "%{http_code}" "$PUBLIC_URL" || echo "000")"
# Cloudflare WAF/Bot-Fight bloqueia legitimamente IPs de datacenter (runners CI)
# com 403/503 — isso é segurança funcionando, não falha. Validamos headers
# públicos por scanner third-party (Mozilla Observatory) em vez de bypass do WAF.
CF_WAF_BLOCKED=0
if [[ "$public_status" =~ ^[23] ]]; then
  echo "[OK] Public domain reachable (${public_status})"
elif [[ "$public_status" == "403" || "$public_status" == "503" ]]; then
  echo "[INFO] Public URL returned ${public_status} — Cloudflare WAF bloqueia IPs de datacenter (CI runners). Isso é comportamento esperado de segurança."
  CF_WAF_BLOCKED=1
else
  echo "[FAIL] Public domain unreachable (${public_status})"
  EXIT_CODE=1
fi
echo

if [[ $CF_WAF_BLOCKED -eq 1 ]]; then
  echo "=== Headers via Mozilla Observatory API (third-party scanner) ==="
  HOST="${PUBLIC_URL#https://}"; HOST="${HOST%%/*}"
  # Inicia novo scan e busca grade via Mozilla Observatory v2 API
  obs_json="$(curl "${CURL_OPTS[@]}" -X POST "https://observatory.mozilla.org/api/v2/scan?host=${HOST}" || echo '{}')"
  grade="$(printf '%s' "$obs_json" | python3 -c "import sys,json
try:
  print(json.load(sys.stdin).get('grade','?'))
except Exception:
  print('?')" 2>/dev/null)"
  if [[ "$grade" =~ ^A ]]; then
    echo "[OK] Mozilla Observatory grade: ${grade}"
  elif [[ "$grade" =~ ^B ]]; then
    echo "[WARN] Mozilla Observatory grade: ${grade} (aceitável; meta=A)"
  else
    echo "[FAIL] Mozilla Observatory grade: ${grade:-indisponível}"
    EXIT_CODE=1
  fi
else
  headers="$(curl "${CURL_OPTS[@]}" -I "$PUBLIC_URL" | tr '[:upper:]' '[:lower:]')"
  echo "=== Headers via direct request ==="
  for hdr in "${REQUIRED_HEADERS[@]}"; do
    if grep -q "^${hdr}:" <<<"$headers"; then
      echo "[OK] ${hdr}"
    else
      echo "[FAIL] Missing header: ${hdr}"
      EXIT_CODE=1
    fi
  done
fi

if [[ $EXIT_CODE -eq 0 ]]; then
  echo "Security header baseline passed."
else
  echo "Security header baseline failed."
fi

exit $EXIT_CODE
