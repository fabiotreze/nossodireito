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

variable "enable_keyvault_private_network" {
  description = "Habilita Private Endpoint e Private DNS para o Key Vault"
  type        = bool
  default     = true
}

variable "key_vault_public_network_access_enabled" {
  description = "Mantém o Key Vault acessível publicamente. Para o modo final fechado, defina false e execute o apply de dentro da VNet."
  type        = bool
  default     = false
}

variable "key_vault_purge_protection_enabled" {
  description = "Habilita purge protection no Key Vault. Recomendado true em PROD; false aceitável em DEV/POC para permitir recriação rápida. Ativado em PROD desde 2026-05-31."
  type        = bool
  default     = true
}

variable "key_vault_soft_delete_retention_days" {
  description = "Período (em dias) de soft-delete do Key Vault. Min 7, max 90. Recomendado >=30 em PROD."
  type        = number
  default     = 7

  validation {
    condition     = var.key_vault_soft_delete_retention_days >= 7 && var.key_vault_soft_delete_retention_days <= 90
    error_message = "soft_delete_retention_days deve estar entre 7 e 90."
  }
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

variable "deployer_object_id" {
  description = "Object ID do principal (user ou SP) que executa Terraform e precisa de acesso ao Key Vault. Se vazio, usa o usuário corrente (data.azurerm_client_config). Em CI/CD, setar para o objectId do Service Principal usado pelo pipeline."
  type        = string
  default     = ""
}

variable "monthly_budget_amount" {
  description = "Valor mensal do budget (na currency do billing account). 0 = não cria budget."
  type        = number
  default     = 0
}

variable "budget_alert_threshold" {
  description = "Percentual do budget que dispara alerta (ex: 70 = 70%)"
  type        = number
  default     = 70
}

variable "enable_openai_private_network" {
  description = "Habilita acesso privado ao Azure OpenAI via Private Endpoint + Private DNS + integração VNet do App Service"
  type        = bool
  default     = true
}

variable "enable_cloudflare_only_inbound" {
  description = "Restringe o App Service público aos IPs de saída da Cloudflare"
  type        = bool
  default     = true
}

variable "vnet_address_space" {
  description = "CIDR da VNet usada para integração do App Service e Private Endpoint do OpenAI"
  type        = list(string)
  default     = ["10.42.0.0/16"]
}

variable "app_service_integration_subnet_cidr" {
  description = "CIDR da subnet delegada para integração VNet do App Service"
  type        = string
  default     = "10.42.1.0/24"
}

variable "openai_private_endpoint_subnet_cidr" {
  description = "CIDR da subnet dedicada ao Private Endpoint do Azure OpenAI"
  type        = string
  default     = "10.42.2.0/24"
}

variable "openai_private_dns_zone_name" {
  description = "Private DNS Zone para resolução privada do endpoint OpenAI"
  type        = string
  default     = "privatelink.openai.azure.com"
}

variable "enable_redis" {
  description = "Habilita Azure Cache for Redis para rate limiting e estudos de PE"
  type        = bool
  default     = true
}

variable "manage_redis_secret_with_terraform" {
  description = "Gerencia o segredo redis-primary-key via Terraform. Em Key Vault privado com runner fora da VNet, mantenha false para evitar erro 403 no plan/apply."
  type        = bool
  default     = false
}

variable "enable_redis_private_network" {
  description = "Habilita Private Endpoint e Private DNS para o Redis"
  type        = bool
  default     = true
}

variable "redis_sku_name" {
  description = "SKU do Azure Cache for Redis"
  type        = string
  default     = "Basic"
}

variable "redis_family" {
  description = "Família do SKU do Azure Cache for Redis"
  type        = string
  default     = "C"
}

variable "redis_capacity" {
  description = "Capacidade do Azure Cache for Redis (0 para Basic C0)"
  type        = number
  default     = 0
}

variable "redis_private_endpoint_subnet_cidr" {
  description = "CIDR da subnet dedicada ao Private Endpoint do Redis"
  type        = string
  default     = "10.42.4.0/24"
}

variable "redis_private_dns_zone_name" {
  description = "Private DNS Zone para resolução privada do endpoint Redis"
  type        = string
  default     = "privatelink.redis.cache.windows.net"
}

variable "keyvault_private_endpoint_subnet_cidr" {
  description = "CIDR da subnet dedicada ao Private Endpoint do Key Vault"
  type        = string
  default     = "10.42.3.0/24"
}

variable "keyvault_private_dns_zone_name" {
  description = "Private DNS Zone para resolução privada do endpoint Key Vault"
  type        = string
  default     = "privatelink.vaultcore.azure.net"
}

# --- Locals: nomes derivados do ambiente ---
locals {
  # Base do projeto — alterando aqui, todos os nomes mudam automaticamente
  project = var.project_name

  # prod usa nomes limpos, outros ambientes ganham sufixo
  suffix                  = var.environment == "prod" ? "" : "-${var.environment}"
  resource_group_name     = "rg-${local.project}${local.suffix}"
  app_service_plan_name   = "plan-${local.project}${local.suffix}"
  web_app_name            = "app-${local.project}${local.suffix}"
  key_vault_name          = "kv-${local.project}${local.suffix}"
  app_insights_name       = "appi-${local.project}${local.suffix}"
  log_analytics_name      = "log-${local.project}${local.suffix}"
  vnet_name               = "vnet-${local.project}${local.suffix}"
  appsvc_subnet_name      = "snet-appsvc-${var.environment}"
  openai_pe_subnet_name   = "snet-openai-pe-${var.environment}"
  keyvault_pe_subnet_name = "snet-kv-pe-${var.environment}"
  redis_pe_subnet_name    = "snet-redis-pe-${var.environment}"
  redis_name              = "redis-${local.project}${local.suffix}"

  cloudflare_ipv4_ranges = [
    "103.21.244.0/22",
    "103.22.200.0/22",
    "103.31.4.0/22",
    "104.16.0.0/13",
    "104.24.0.0/14",
    "108.162.192.0/18",
    "131.0.72.0/22",
    "141.101.64.0/18",
    "162.158.0.0/15",
    "172.64.0.0/13",
    "173.245.48.0/20",
    "188.114.96.0/20",
    "190.93.240.0/20",
    "197.234.240.0/22",
    "198.41.128.0/17",
  ]

  cloudflare_ipv6_ranges = [
    "2400:cb00::/32",
    "2606:4700::/32",
    "2803:f800::/32",
    "2405:b500::/32",
    "2405:8100::/32",
    "2a06:98c0::/29",
    "2c0f:f248::/32",
  ]

  cloudflare_allowed_ip_ranges = concat(local.cloudflare_ipv4_ranges, local.cloudflare_ipv6_ranges)

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
