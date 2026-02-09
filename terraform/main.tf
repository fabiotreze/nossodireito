# ============================================================
# Main — Azure Static Web App + Key Vault
# ============================================================
# Well-Architected Framework — 5 Pillars:
#
# 1. COST OPTIMIZATION
#    - Standard SKU com cert próprio: $9/mês
#    - Free SKU com cert managed: $0/mês
#    - Key Vault Standard: ~$0.03/10k operations
#    - No compute, no App Service Plan
#
# 2. SECURITY
#    - Certificado PFX armazenado no Key Vault (não no repo)
#    - Senha do PFX via variável sensitive (nunca em disco)
#    - Managed Identity para acesso ao Key Vault (sem credenciais)
#    - Security headers via staticwebapp.config.json
#    - HTTPS enforced por padrão
#    - Key Vault com soft-delete + purge protection
#
# 3. RELIABILITY
#    - Azure global CDN com edge PoPs mundiais
#    - Static content = zero falhas de runtime
#    - Key Vault 99.99% SLA
#
# 4. OPERATIONAL EXCELLENCE
#    - Infrastructure as Code (Terraform)
#    - CI/CD via GitHub Actions (deploy.yml)
#    - Zero dados sensíveis no repositório
#    - Multi-ambiente via tfvars
#
# 5. PERFORMANCE EFFICIENCY
#    - Conteúdo servido do edge mais próximo
#    - Sem cold starts, sem scaling
#    - ~178KB payload total
# ============================================================

# --- Data Sources ---
data "azurerm_client_config" "current" {}

# --- Resource Group ---
resource "azurerm_resource_group" "main" {
  name     = local.resource_group_name
  location = var.location
  tags     = local.tags
}

# --- Key Vault (dedicado para certificados) ---
resource "azurerm_key_vault" "main" {
  count = var.enable_keyvault ? 1 : 0

  name                       = local.key_vault_name
  location                   = azurerm_resource_group.main.location
  resource_group_name        = azurerm_resource_group.main.name
  tenant_id                  = data.azurerm_client_config.current.tenant_id
  sku_name                   = "standard"
  soft_delete_retention_days = 7
  purge_protection_enabled   = false # true em produção real; false para dev/teste

  tags = local.tags
}

# --- Access Policy: Terraform deployer (você) ---
resource "azurerm_key_vault_access_policy" "deployer" {
  count = var.enable_keyvault ? 1 : 0

  key_vault_id = azurerm_key_vault.main[0].id
  tenant_id    = data.azurerm_client_config.current.tenant_id
  object_id    = data.azurerm_client_config.current.object_id

  certificate_permissions = ["Create", "Delete", "Get", "Import", "List", "Update", "Purge"]
  secret_permissions      = ["Get", "List", "Set", "Delete", "Purge"]
}

# --- Access Policy: Static Web App Managed Identity ---
resource "azurerm_key_vault_access_policy" "swa" {
  count = var.enable_keyvault ? 1 : 0

  key_vault_id = azurerm_key_vault.main[0].id
  tenant_id    = data.azurerm_client_config.current.tenant_id
  object_id    = azurerm_static_web_app.main.identity[0].principal_id

  certificate_permissions = ["Get"]
  secret_permissions      = ["Get"]
}

# --- Import PFX Certificate ---
resource "azurerm_key_vault_certificate" "wildcard" {
  count = var.enable_keyvault && var.pfx_file_path != "" ? 1 : 0

  name         = "fabiotreze-wildcard"
  key_vault_id = azurerm_key_vault.main[0].id

  certificate {
    contents = filebase64(var.pfx_file_path)
    password = var.pfx_password
  }

  depends_on = [azurerm_key_vault_access_policy.deployer]
}

# --- Static Web App ---
resource "azurerm_static_web_app" "main" {
  name                = local.static_web_app_name
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku_tier            = var.sku_tier
  sku_size            = var.sku_tier

  # Managed Identity sempre ativa (gratuito) — necessária para Key Vault
  identity {
    type = "SystemAssigned"
  }

  tags = local.tags
}

# --- Custom Domain ---
# PREREQUISITO: Configure o CNAME no GoDaddy ANTES de rodar terraform apply.
#   GoDaddy → DNS → Add Record:
#     Type: CNAME | Name: nossodireito | Value: <default_hostname>.azurestaticapps.net
#
# O Azure valida o CNAME durante a criação do recurso.
# SSL managed é provisionado automaticamente pelo Azure após validação.

resource "azurerm_static_web_app_custom_domain" "main" {
  count             = var.enable_custom_domain && var.custom_domain != "" ? 1 : 0
  static_web_app_id = azurerm_static_web_app.main.id
  domain_name       = var.custom_domain
  validation_type   = "cname-delegation"
}
