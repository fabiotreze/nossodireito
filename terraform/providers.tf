# ============================================================
# NossoDireito — Terraform — Azure App Service + Key Vault
# ============================================================
# Well-Architected Framework alignment:
#   - Cost Optimization: B1 Linux ~$13/mês
#   - Security: BYOC (PFX via Key Vault), SNI SSL, HTTPS Only
#   - Reliability: 99.95% SLA, always_on, health check
#   - Operational Excellence: IaC + CI/CD auto-deploy
#   - Performance: Node.js 22 LTS, HTTP/2, Brotli + gzip
# ============================================================

terraform {
  # Terraform version — testado e validado em 1.15.5 (2026-05-29)
  # Upgrade: brew upgrade terraform
  # CI/CD usa OIDC sem access keys
  required_version = ">= 1.6, <= 2.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.74" # Locked a 4.74.0 (2026-05-29)
      # Pin habilitado via .terraform.lock.hcl para reproducibilidade
      # Atualizações de provider: terraform init -upgrade
    }
  }

  # Backend remoto Azure Storage com lock nativo (provisionado em 2026-05-31).
  # Storage Account: stnossodireitobr (RG rg-tfstate-nossodireito, brazilsouth).
  # Auth via Azure AD (sem access key armazenada). Guia: BACKEND-REMOTE.md.
  backend "azurerm" {
    resource_group_name  = "rg-tfstate-nossodireito"
    storage_account_name = "stnossodireitobr"
    container_name       = "tfstate"
    key                  = "nossodireito.prod.tfstate"
    use_azuread_auth     = true
  }
}

provider "azurerm" {
  subscription_id                 = var.subscription_id
  resource_provider_registrations = "core"

  features {
    key_vault {
      purge_soft_delete_on_destroy    = true
      recover_soft_deleted_key_vaults = true
    }
  }
}
