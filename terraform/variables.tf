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

variable "project_name" {
  description = "Nome base do projeto. Todos os recursos Azure derivam deste nome (rg-<name>, app-<name>, etc.)."
  type        = string
  default     = "nossodireito-br"

  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.project_name)) && length(var.project_name) <= 20
    error_message = "project_name deve conter apenas letras minúsculas, números e hífens (max 20 chars para respeitar limites do Key Vault)."
  }
}

variable "location" {
  description = "Região Azure Brasil (LGPD — dados devem permanecer em território nacional)"
  type        = string
  default     = "brazilsouth"
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
  # Base do projeto — alterando aqui, todos os nomes mudam automaticamente
  project = var.project_name

  # prod usa nomes limpos, outros ambientes ganham sufixo
  suffix                = var.environment == "prod" ? "" : "-${var.environment}"
  resource_group_name   = "rg-${local.project}${local.suffix}"
  app_service_plan_name = "plan-${local.project}${local.suffix}"
  web_app_name          = "app-${local.project}${local.suffix}"
  key_vault_name        = "kv-${local.project}${local.suffix}"
  app_insights_name     = "appi-${local.project}${local.suffix}"
  log_analytics_name    = "log-${local.project}${local.suffix}"

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
