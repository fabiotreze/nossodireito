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
      version = "~> 4.74"  # Locked a 4.74.0 (2026-05-29)
      # Pin habilitado via .terraform.lock.hcl para reproducibilidade
      # Atualizações de provider: terraform init -upgrade
    }
  }

  # Backend local por padrão.
  # State é persistido como artifact no GitHub Actions
  # (.github/workflows/terraform.yml).
  #
  # Migração para backend remoto Azure Storage com lock nativo é opt-in;
  # ver guia operacional em BACKEND-REMOTE.md (mesma pasta).
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
