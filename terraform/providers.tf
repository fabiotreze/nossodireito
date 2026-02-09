# ============================================================
# NossoDireito — Terraform — Azure Static Web App
# ============================================================
# Well-Architected Framework alignment:
#   - Cost Optimization: Free tier, zero compute cost
#   - Security: Managed SSL, security headers via config
#   - Reliability: Azure global CDN with auto-failover
#   - Operational Excellence: IaC + CI/CD auto-deploy
#   - Performance: Edge-distributed static content
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
  resource_provider_registrations = "none"

  features {
    key_vault {
      purge_soft_delete_on_destroy    = true
      recover_soft_deleted_key_vaults = true
    }
  }
}
