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

  # HCP Terraform (free) — armazena tfstate remotamente sem Storage Account.
  # Setup:
  #   1. Crie conta grátis: https://app.terraform.io/signup
  #   2. Crie organização "fabiotreze" e workspace "nossodireito"
  #   3. No workspace: Settings → General → Execution Mode = "Local"
  #      (GitHub Actions roda o plan/apply, HCP só guarda o state)
  #   4. Gere API token: User Settings → Tokens → Create API token
  #   5. GitHub repo → Settings → Secrets → TF_API_TOKEN
  cloud {
    organization = "fabiotreze"

    workspaces {
      name = "nossodireito"
    }
  }
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
