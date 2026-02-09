# ============================================================
# Variables — Multi-environment support
# ============================================================
# Para novo ambiente, basta criar um terraform.tfvars diferente:
#   terraform apply -var-file="staging.tfvars"
# ============================================================

variable "subscription_id" {
  description = "Azure Subscription ID"
  type        = string
  sensitive   = true
}

variable "environment" {
  description = "Nome do ambiente (prod, staging, dev). Usado nos nomes dos recursos."
  type        = string
  default     = "prod"

  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.environment))
    error_message = "Environment deve conter apenas letras minúsculas, números e hífens."
  }
}

variable "location" {
  description = "Região Azure (conteúdo distribuído globalmente via CDN)"
  type        = string
  default     = "eastus2"
}

variable "sku_tier" {
  description = "Tier do Static Web App: 'Free' ($0) ou 'Standard' ($9/mês, necessário para SSL próprio)"
  type        = string
  default     = "Standard"

  validation {
    condition     = contains(["Free", "Standard"], var.sku_tier)
    error_message = "SKU deve ser 'Free' ou 'Standard'."
  }
}

variable "custom_domain" {
  description = "Domínio customizado. Deixe vazio para usar apenas o domínio Azure."
  type        = string
  default     = "nossodireito.fabiotreze.com"
}

variable "enable_custom_domain" {
  description = "Habilitar domínio customizado (requer CNAME configurado no DNS)"
  type        = bool
  default     = true
}

variable "github_repo_url" {
  description = "URL do repositório GitHub"
  type        = string
  default     = "https://github.com/fabiotreze/nossodireito"
}

variable "github_repo_branch" {
  description = "Branch principal do repositório"
  type        = string
  default     = "main"
}

variable "extra_tags" {
  description = "Tags adicionais para os recursos (merge com tags padrão)"
  type        = map(string)
  default     = {}
}

# --- Certificado SSL (PFX) ---
variable "pfx_file_path" {
  description = "Caminho do arquivo PFX do certificado SSL. Não será commitado no repositório."
  type        = string
  default     = ""
}

variable "pfx_password" {
  description = "Senha do certificado PFX. Informar via -var, TF_VAR_pfx_password, ou GitHub Actions secret."
  type        = string
  sensitive   = true
  default     = ""
}

variable "enable_keyvault" {
  description = "Criar Key Vault dedicado para armazenar o certificado SSL"
  type        = bool
  default     = true
}

# --- Locals: nomes derivados do ambiente ---
locals {
  name_prefix = "nossodireito-${var.environment}"

  # prod usa nomes limpos, outros ambientes ganham sufixo
  resource_group_name = var.environment == "prod" ? "rg-nossodireito" : "rg-nossodireito-${var.environment}"
  static_web_app_name = var.environment == "prod" ? "stapp-nossodireito" : "stapp-nossodireito-${var.environment}"
  key_vault_name      = var.environment == "prod" ? "kv-nossodireito" : "kv-nossodireito-${var.environment}"

  tags = merge(
    {
      project     = "nossodireito"
      environment = var.environment
      managed_by  = "terraform"
      purpose     = "pcd-rights-portal"
    },
    var.extra_tags
  )
}
