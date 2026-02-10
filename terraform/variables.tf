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

variable "app_service_sku" {
  description = "SKU do App Service Plan: 'B1' ($13/mês, suporta custom SSL) ou 'F1' (Free, sem custom SSL)"
  type        = string
  default     = "B1"

  validation {
    condition     = contains(["F1", "B1", "B2", "B3", "S1", "S2", "S3", "P1v3", "P2v3"], var.app_service_sku)
    error_message = "SKU deve ser F1, B1, B2, B3, S1, S2, S3, P1v3 ou P2v3."
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

variable "web_rp_object_id" {
  description = "Object ID do Service Principal Microsoft.Web RP (abfa0a7c-a6b6-4736-8310-5855508787cd). Descoberto via az ad sp show."
  type        = string
  default     = ""
}

variable "user_object_id" {
  description = "Object ID da sua conta pessoal Azure AD (para acesso ao portal, KV, App Service etc.). Descoberto via Portal > Entra ID > Users."
  type        = string
  default     = ""
}

variable "alert_email" {
  description = "E-mail para receber alertas de monitoramento do Azure Monitor"
  type        = string
  default     = ""
}

# --- Locals: nomes derivados do ambiente ---
locals {
  name_prefix = "nossodireito-${var.environment}"

  # prod usa nomes limpos, outros ambientes ganham sufixo
  resource_group_name   = var.environment == "prod" ? "rg-nossodireito" : "rg-nossodireito-${var.environment}"
  app_service_plan_name = var.environment == "prod" ? "plan-nossodireito" : "plan-nossodireito-${var.environment}"
  web_app_name          = var.environment == "prod" ? "app-nossodireito" : "app-nossodireito-${var.environment}"
  key_vault_name        = var.environment == "prod" ? "kv-nossodireito" : "kv-nossodireito-${var.environment}"
  app_insights_name     = var.environment == "prod" ? "appi-nossodireito" : "appi-nossodireito-${var.environment}"
  log_analytics_name    = var.environment == "prod" ? "log-nossodireito" : "log-nossodireito-${var.environment}"

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
