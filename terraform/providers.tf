# ============================================================
# NossoDireito — Terraform — Azure Static Web App (Free)
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

  # Local state. For team use, configure remote backend:
  # backend "azurerm" {
  #   resource_group_name  = "terraform-state-rg"
  #   storage_account_name = "nossodireitotfstate"
  #   container_name       = "tfstate"
  #   key                  = "nossodireito.tfstate"
  #   use_azuread_auth     = true
  # }
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
