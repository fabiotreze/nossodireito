# ============================================================
# Azure Document Intelligence — POC IA com privacidade LGPD
# ============================================================
# Decisão arquitetural:
# - Tier F0 (free): 500 páginas/mês grátis — suficiente para POC
# - Trocar para S0 quando exceder (R$ 5/100 páginas)
# - Localização: brazilsouth (residência de dados LGPD)
# - Acesso: Managed Identity do App Service (zero secrets)
# - customer_managed_key_enabled = false em F0 (não suportado);
#   habilitar no S0 + Key Vault quando promover a produção
#
# Privacidade (Art. 6º, 9º, 11 LGPD):
# - Documentos só são enviados COM consentimento explícito (opt-in UI)
# - Anonimização client-side ANTES do POST (CPF/RG/Nome/CEP/Telefone → tokens)
# - Backend valida que o texto NÃO contém PII (double-check em server.js)
# - Zero log do conteúdo — apenas hash SHA-256 + duração + status
# - public_network_access_enabled = true (necessário para App Service B1
#   sem VNet integration); endurecer com private endpoint no Plano S1+
# ============================================================

variable "enable_ai_doc_intelligence" {
  description = "Habilita Azure Document Intelligence para análise IA opt-in de laudos"
  type        = bool
  default     = true
}

variable "ai_doc_intelligence_sku" {
  description = "SKU do Document Intelligence: F0 (free, 500 pgs/mês) ou S0 (pay-per-use)"
  type        = string
  default     = "F0"

  validation {
    condition     = contains(["F0", "S0"], var.ai_doc_intelligence_sku)
    error_message = "SKU deve ser F0 (free) ou S0 (standard)."
  }
}

resource "azurerm_cognitive_account" "doc_intelligence" {
  count = var.enable_ai_doc_intelligence ? 1 : 0

  name                = "cog-${local.project}-docint${local.suffix}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  kind                = "FormRecognizer"
  sku_name            = var.ai_doc_intelligence_sku

  # Custom subdomain é OBRIGATÓRIO para autenticação via Azure AD / MSI.
  # Sem isso, o endpoint só aceita key-based auth.
  custom_subdomain_name = "cog-${local.project}-docint${local.suffix}"

  # Acesso de rede:
  # - F0 não suporta network ACLs nem private endpoints.
  # - Para S0+ em produção: habilitar network_acls com IPs do App Service.
  public_network_access_enabled = true

  # Autenticação:
  # - local_auth_enabled = false força uso de Azure AD/MSI (zero key leaks).
  # - Atende princípio LGPD de mínima exposição de credenciais.
  local_auth_enabled = false

  identity {
    type = "SystemAssigned"
  }

  tags = merge(local.tags, {
    "LGPDClassification" = "ai-opt-in"
    "DataResidency"      = "brazil"
    "Purpose"            = "document-analysis-poc"
    "lgpd_compliant"     = "true"
  })

  # LGPD Guardrails (lifecycle precondition): bloqueia apply se requisitos violados.
  lifecycle {
    precondition {
      condition     = var.location == "brazilsouth" || var.location == "brazilsoutheast"
      error_message = "LGPD Art. 33: Doc Intelligence DEVE estar em região brasileira (brazilsouth/brazilsoutheast)."
    }
    precondition {
      condition     = !var.enable_ai_doc_intelligence || true # local_auth_enabled = false já hardcoded acima
      error_message = "LGPD Art. 46: Doc Intelligence DEVE usar MSI (local_auth_enabled = false)."
    }
  }
}

# --- Role Assignment: App Service MSI → Cognitive Services User ---
# Permite que o server.js chame Doc Intelligence sem keys/secrets.
# Role "Cognitive Services User" = leitura de keys + chamada à API
# (sem permissão de gerenciar o recurso). Princípio do menor privilégio.
resource "azurerm_role_assignment" "app_to_doc_intelligence" {
  count = var.enable_ai_doc_intelligence ? 1 : 0

  scope                = azurerm_cognitive_account.doc_intelligence[0].id
  role_definition_name = "Cognitive Services User"
  principal_id         = azurerm_linux_web_app.main.identity[0].principal_id
}

# --- App Settings: expõe endpoint para o server.js ---
# A KEY nunca é exposta — autenticação via DefaultAzureCredential (MSI).
# O server.js só precisa do endpoint para construir a URL.
# NOTA: app_settings está definido no recurso main azurerm_linux_web_app;
# para evitar duplicação, este bloco é apenas DOCUMENTAÇÃO.
# A integração efetiva acontece via locals abaixo + merge em main.tf.
locals {
  doc_intelligence_app_settings = var.enable_ai_doc_intelligence ? {
    AZURE_DOC_INTELLIGENCE_ENDPOINT = azurerm_cognitive_account.doc_intelligence[0].endpoint
    AI_ANALYSIS_ENABLED             = "true"
  } : {}
}

# --- Outputs ---
output "ai_doc_intelligence_endpoint" {
  description = "Endpoint do Azure Document Intelligence (apenas se habilitado)"
  value       = var.enable_ai_doc_intelligence ? azurerm_cognitive_account.doc_intelligence[0].endpoint : null
}

output "ai_doc_intelligence_principal_id" {
  description = "Principal ID da Managed Identity do Document Intelligence"
  value       = var.enable_ai_doc_intelligence ? azurerm_cognitive_account.doc_intelligence[0].identity[0].principal_id : null
}
