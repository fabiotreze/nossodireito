#!/usr/bin/env bash
set -euo pipefail

# Bootstrap automation for replicating NossoDireito in a new tenant/subscription.
# Creates/updates GitHub secrets and writes a ready-to-use terraform tfvars file.

readonly SCRIPT_NAME="$(basename "$0")"

usage() {
  cat <<'USAGE'
Usage:
  scripts/bootstrap_replication.sh \
    --subscription-id <sub-id> \
    --tenant-id <tenant-id> \
    --client-id <app-client-id> \
    --project-name <name> \
    --custom-domain <domain> \
    [--environment <prod|staging|dev>] \
    [--location <azure-region>] \
    [--repo <owner/repo>] \
    [--output-tfvars <path>] \
    [--enable-custom-domain <true|false>] \
    [--enable-keyvault <true|false>]

Example:
  scripts/bootstrap_replication.sh \
    --subscription-id 00000000-0000-0000-0000-000000000000 \
    --tenant-id 11111111-1111-1111-1111-111111111111 \
    --client-id 22222222-2222-2222-2222-222222222222 \
    --project-name nossodireito-br \
    --custom-domain nossodireito.contoso.com
USAGE
}

require_cmd() {
  local cmd="$1"
  command -v "$cmd" >/dev/null 2>&1 || {
    echo "[ERROR] Missing command: $cmd" >&2
    exit 1
  }
}

SUBSCRIPTION_ID=""
TENANT_ID=""
CLIENT_ID=""
PROJECT_NAME=""
CUSTOM_DOMAIN=""
ENVIRONMENT="prod"
LOCATION="brazilsouth"
REPO="fabiotreze/nossodireito"
OUTPUT_TFVARS="terraform/replication.auto.tfvars"
ENABLE_CUSTOM_DOMAIN="true"
ENABLE_KEYVAULT="true"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --subscription-id) SUBSCRIPTION_ID="$2"; shift 2 ;;
    --tenant-id) TENANT_ID="$2"; shift 2 ;;
    --client-id) CLIENT_ID="$2"; shift 2 ;;
    --project-name) PROJECT_NAME="$2"; shift 2 ;;
    --custom-domain) CUSTOM_DOMAIN="$2"; shift 2 ;;
    --environment) ENVIRONMENT="$2"; shift 2 ;;
    --location) LOCATION="$2"; shift 2 ;;
    --repo) REPO="$2"; shift 2 ;;
    --output-tfvars) OUTPUT_TFVARS="$2"; shift 2 ;;
    --enable-custom-domain) ENABLE_CUSTOM_DOMAIN="$2"; shift 2 ;;
    --enable-keyvault) ENABLE_KEYVAULT="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *)
      echo "[ERROR] Unknown option: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if [[ -z "$SUBSCRIPTION_ID" || -z "$TENANT_ID" || -z "$CLIENT_ID" || -z "$PROJECT_NAME" || -z "$CUSTOM_DOMAIN" ]]; then
  echo "[ERROR] Required parameters are missing." >&2
  usage
  exit 1
fi

require_cmd gh
require_cmd az

if [[ ! -f "terraform/terraform.tfvars.example" ]]; then
  echo "[ERROR] Run this script from repository root (terraform/terraform.tfvars.example not found)." >&2
  exit 1
fi

echo "[1/4] Setting GitHub Actions secrets for ${REPO}"
gh secret set ARM_SUBSCRIPTION_ID --repo "$REPO" --body "$SUBSCRIPTION_ID"
gh secret set ARM_TENANT_ID --repo "$REPO" --body "$TENANT_ID"
gh secret set ARM_CLIENT_ID --repo "$REPO" --body "$CLIENT_ID"

echo "[2/4] Ensuring Azure CLI context"
az account set --subscription "$SUBSCRIPTION_ID" >/dev/null

echo "[3/4] Writing ${OUTPUT_TFVARS}"
mkdir -p "$(dirname "$OUTPUT_TFVARS")"
cat > "$OUTPUT_TFVARS" <<EOF
subscription_id       = "${SUBSCRIPTION_ID}"
environment           = "${ENVIRONMENT}"
project_name          = "${PROJECT_NAME}"
location              = "${LOCATION}"
custom_domain         = "${CUSTOM_DOMAIN}"
enable_custom_domain  = ${ENABLE_CUSTOM_DOMAIN}
enable_keyvault       = ${ENABLE_KEYVAULT}
EOF

echo "[4/4] Next actions"
echo "- Configure Cloudflare CNAME: ${CUSTOM_DOMAIN} -> app-${PROJECT_NAME}.azurewebsites.net"
echo "- Set SSL mode to Full (strict) in Cloudflare"
echo "- If using PFX, set GitHub secrets: PFX_BASE64 and TF_VAR_PFX_PASSWORD"
echo "- Run: gh workflow run terraform.yml -R ${REPO} -f action=apply"

echo "[DONE] Bootstrap completed successfully."
