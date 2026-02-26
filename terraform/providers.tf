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
  required_version = ">= 1.6"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
  }

  # Backend local — sem remote state.
  # O state é salvo como artifact no GitHub Actions para persistência.
  # Para destroy, baixe o artifact antes de rodar.
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
