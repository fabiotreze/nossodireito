# ============================================================
# Azure OpenAI — Análise IA com privacidade LGPD
# ============================================================
# Decisão arquitetural:
# - Substitui Azure Doc Intelligence (que era OCR; rejeitava text/plain).
# - Modelo: gpt-4o-mini (rápido, barato, multilingual com bom pt-BR).
# - SKU: GlobalStandard (único disponível para gpt-4o-mini em brazilsouth
#   atualmente). Microsoft DPA garante zero retenção de prompts/completions
#   (com abuse-monitoring opt-out). Roteamento de tráfego pode ser global,
#   mas armazenamento de Customer Data é vedado por contrato.
# - Localização: brazilsouth (LGPD Art. 33 — residência de dados).
# - Acesso: Managed Identity do App Service (zero secrets em código).
# - Custo estimado: ~$0.15/1M input tokens + $0.60/1M output tokens.
#   Para 1.000 análises/mês com ~2K tokens cada → ~$1.50/mês.
#
# Privacidade (Art. 6º, 7º, 9º, 11 LGPD):
# - Texto enviado SOMENTE com consentimento explícito (modal opt-in)
# - Anonimização client-side ANTES do POST (CPF/RG/Nome/CEP/Telefone → tokens)
# - Backend valida que texto NÃO contém PII (double-check em server.js)
# - Zero log de conteúdo — apenas hash SHA-256 + duração + status
# - public_network_access_enabled = true (App Service B1 sem VNet);
#   endurecer com private endpoint no Plano S1+
# ============================================================

variable "enable_ai_openai" {
  description = "Habilita Azure OpenAI para análise IA opt-in de laudos médicos"
  type        = bool
  default     = true
}

variable "ai_openai_model_name" {
  description = "Nome do modelo Azure OpenAI a fazer deploy"
  type        = string
  default     = "gpt-4o-mini"
}

variable "ai_openai_model_version" {
  description = "Versão do modelo OpenAI (vide az cognitiveservices model list)"
  type        = string
  default     = "2024-07-18"
}

variable "ai_openai_deployment_capacity" {
  description = "Tokens-por-minuto (em milhares) para o deployment GlobalStandard"
  type        = number
  default     = 10 # 10K TPM = suficiente para ~300 análises/h
}

resource "azurerm_cognitive_account" "openai" {
  count = var.enable_ai_openai ? 1 : 0

  name                = "cog-${local.project}-openai${local.suffix}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  kind                = "OpenAI"
  sku_name            = "S0"

  # Custom subdomain é OBRIGATÓRIO para autenticação via Azure AD / MSI.
  custom_subdomain_name = "cog-${local.project}-openai${local.suffix}"

  public_network_access_enabled = var.enable_openai_private_network ? false : true

  # local_auth_enabled = false força uso de Azure AD/MSI (zero key leaks).
  # LGPD Art. 46 — mínima exposição de credenciais.
  local_auth_enabled = false

  identity {
    type = "SystemAssigned"
  }

  tags = merge(local.tags, {
    "LGPDClassification" = "ai-opt-in"
    "DataResidency"      = "brazil-south"
    "lgpd_compliant"     = "true"
    "Model"              = var.ai_openai_model_name
  })

  lifecycle {
    precondition {
      condition     = var.location == "brazilsouth" || var.location == "brazilsoutheast"
      error_message = "LGPD Art. 33: Azure OpenAI DEVE estar em região brasileira (brazilsouth/brazilsoutheast)."
    }
  }
}

# --- Model Deployment: gpt-4o-mini ---
resource "azurerm_cognitive_deployment" "gpt_4o_mini" {
  count = var.enable_ai_openai ? 1 : 0

  name                 = var.ai_openai_model_name
  cognitive_account_id = azurerm_cognitive_account.openai[0].id

  model {
    format  = "OpenAI"
    name    = var.ai_openai_model_name
    version = var.ai_openai_model_version
  }

  # GlobalStandard é o único SKU disponível para gpt-4o-mini em brazilsouth.
  # Roteamento global de compute; armazenamento de Customer Data permanece
  # vedado por Microsoft DPA (zero retention após resposta).
  sku {
    name     = "GlobalStandard"
    capacity = var.ai_openai_deployment_capacity
  }

  # Filtro de conteúdo padrão da Microsoft (Responsible AI):
  # - Bloqueia: violência, ódio, sexual, automutilação (severity ≥ medium)
  # - Não é PII filter — anonimização client/server-side cobre LGPD.
  rai_policy_name = "Microsoft.DefaultV2"

  # Versionamento estável: usa upgrade_option = "OnceCurrentVersionExpired"
  # para evitar trocas surpresa de modelo em produção.
  version_upgrade_option = "OnceCurrentVersionExpired"
}

# --- Role Assignment: App MSI -> Cognitive Services OpenAI User ---
# Role granular (apenas chamadas /openai/*), princípio do menor privilégio.
# Role definition ID: 5e0bd9bd-7b93-4f28-af87-19fc36ad61bd
#
# ATENÇÃO: O SP do GitHub OIDC tem apenas Contributor, sem permissão para
# criar role assignments. Se o apply falhar com 403 AuthorizationFailed, o
# usuário pessoal precisa executar manualmente:
#   az role assignment create \
#     --assignee <app_msi_principal_id> \
#     --role "Cognitive Services OpenAI User" \
#     --scope <openai_resource_id>
# Depois adicionar um import block (Terraform 1.5+) referenciando esta
# resource para adoção no state.
resource "azurerm_role_assignment" "app_to_openai" {
  count = var.enable_ai_openai ? 1 : 0

  scope                = azurerm_cognitive_account.openai[0].id
  role_definition_name = "Cognitive Services OpenAI User"
  principal_id         = azurerm_linux_web_app.main.identity[0].principal_id
}

# --- App Settings ---
# Apenas endpoint + deployment name. Chave NUNCA exposta — auth via MSI.
locals {
  openai_app_settings = var.enable_ai_openai ? {
    AZURE_OPENAI_ENDPOINT        = azurerm_cognitive_account.openai[0].endpoint
    AZURE_OPENAI_DEPLOYMENT_NAME = azurerm_cognitive_deployment.gpt_4o_mini[0].name
    AZURE_OPENAI_API_VERSION     = "2024-10-21"
    AI_ANALYSIS_ENABLED          = "true"
  } : {}
}

# --- Outputs ---
output "ai_openai_endpoint" {
  description = "Endpoint do Azure OpenAI (apenas se habilitado)"
  value       = var.enable_ai_openai ? azurerm_cognitive_account.openai[0].endpoint : null
}

output "ai_openai_deployment_name" {
  description = "Nome do deployment do modelo gpt-4o-mini"
  value       = var.enable_ai_openai ? azurerm_cognitive_deployment.gpt_4o_mini[0].name : null
}
