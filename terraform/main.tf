# ============================================================
# Main — Azure App Service + Key Vault + Custom SSL (BYOC)
# ============================================================
# Well-Architected Framework — 5 Pillars:
#
# 1. COST OPTIMIZATION
#    - App Service B1 Linux: ~$13/mês
#    - Key Vault Standard: ~$0.03/10k operations
#    - Cert PFX próprio: $0 (já pago)
#    - Total estimado: ~$13/mês
#
# 2. SECURITY
#    - Certificado PFX próprio via Key Vault (BYOC)
#    - SNI SSL binding no custom domain
#    - Managed Identity para acesso ao Key Vault (sem credenciais)
#    - Security headers via server.js middleware
#    - HTTPS Only enforced
#    - FTPS Disabled, SCM basic auth disabled
#
# 3. RELIABILITY
#    - App Service 99.95% SLA (Basic+)
#    - Health check habilitado
#    - always_on = true (sem cold starts)
#
# 4. OPERATIONAL EXCELLENCE
#    - Infrastructure as Code (Terraform)
#    - CI/CD via GitHub Actions (deploy.yml)
#    - Zero dados sensíveis no repositório
#    - Multi-ambiente via tfvars
#
# 5. PERFORMANCE EFFICIENCY
#    - Node.js 22 LTS servindo static files com Express
#    - Gzip compression habilitado
#    - Cache headers configurados por tipo de asset
#    - HTTP/2 habilitado
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
  purge_protection_enabled   = false

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

# --- Access Policy: App Service Managed Identity ---
resource "azurerm_key_vault_access_policy" "app_service" {
  count = var.enable_keyvault ? 1 : 0

  key_vault_id = azurerm_key_vault.main[0].id
  tenant_id    = data.azurerm_client_config.current.tenant_id
  object_id    = azurerm_linux_web_app.main.identity[0].principal_id

  certificate_permissions = ["Get"]
  secret_permissions      = ["Get"]
}

# --- Access Policy: Microsoft.Web RP (necessário para App Service Certificate) ---
# O Azure App Service usa o RP Microsoft.Web (App ID: abfa0a7c-a6b6-4736-8310-5855508787cd)
# para ler o certificado do Key Vault. Sem esta policy, o SSL binding falha com 403.
# O Object ID é descoberto automaticamente pelo workflow via az ad sp show.
resource "azurerm_key_vault_access_policy" "web_rp" {
  count = var.enable_keyvault && var.web_rp_object_id != "" ? 1 : 0

  key_vault_id = azurerm_key_vault.main[0].id
  tenant_id    = data.azurerm_client_config.current.tenant_id
  object_id    = var.web_rp_object_id

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

# --- Log Analytics Workspace (required by App Insights) ---
resource "azurerm_log_analytics_workspace" "main" {
  name                = local.log_analytics_name
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "PerGB2018"
  retention_in_days   = 30

  tags = local.tags
}

# --- Application Insights ---
# Rastreia: page views, IPs de origem, geolocalização, tempos de resposta,
# erros, e métricas de performance. Portal: portal.azure.com > App Insights.
resource "azurerm_application_insights" "main" {
  name                = local.app_insights_name
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  workspace_id        = azurerm_log_analytics_workspace.main.id
  application_type    = "Node.JS"

  tags = local.tags
}

# --- App Service Plan (Linux) ---
resource "azurerm_service_plan" "main" {
  name                = local.app_service_plan_name
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  os_type             = "Linux"
  sku_name            = var.app_service_sku

  tags = local.tags
}

# --- Linux Web App ---
resource "azurerm_linux_web_app" "main" {
  name                = local.web_app_name
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  service_plan_id     = azurerm_service_plan.main.id

  https_only = true

  identity {
    type = "SystemAssigned"
  }

  site_config {
    always_on  = true
    ftps_state = "Disabled"

    application_stack {
      node_version = "22-lts"
    }

    app_command_line                  = "node server.js"
    health_check_path                 = "/health"
    health_check_eviction_time_in_min = 5
    http2_enabled                     = true
  }

  app_settings = {
    WEBSITE_REDIRECT_ALL_TRAFFIC_TO_HTTPS = "1"
    NODE_ENV                              = "production"
    SCM_DO_BUILD_DURING_DEPLOYMENT        = "false"
    APPLICATIONINSIGHTS_CONNECTION_STRING = azurerm_application_insights.main.connection_string
    # Codeless agent DESABILITADO — o server.js já usa o SDK applicationinsights manualmente.
    # Ter ambos causa: "Attempted duplicate registration of API: propagation"
    ApplicationInsightsAgent_EXTENSION_VERSION = "disabled"
  }

  tags = local.tags
}

# --- Custom Domain ---
# PREREQUISITO: Atualize o CNAME no GoDaddy para apontar para <web_app_name>.azurewebsites.net
resource "azurerm_app_service_custom_hostname_binding" "main" {
  count               = var.enable_custom_domain && var.custom_domain != "" ? 1 : 0
  hostname            = var.custom_domain
  app_service_name    = azurerm_linux_web_app.main.name
  resource_group_name = azurerm_resource_group.main.name

  lifecycle {
    ignore_changes = [ssl_state, thumbprint]
  }
}

# --- Access Policy: Usuário pessoal (acesso portal/dados) ---
resource "azurerm_key_vault_access_policy" "user" {
  count = var.enable_keyvault && var.user_object_id != "" ? 1 : 0

  key_vault_id = azurerm_key_vault.main[0].id
  tenant_id    = data.azurerm_client_config.current.tenant_id
  object_id    = var.user_object_id

  certificate_permissions = ["Create", "Delete", "Get", "Import", "List", "Update", "Purge", "Recover"]
  secret_permissions      = ["Get", "List", "Set", "Delete", "Purge", "Recover"]
  key_permissions         = ["Get", "List", "Create", "Delete", "Update", "Purge", "Recover"]
}

# --- App Service Certificate (from Key Vault) ---
# O certificado PFX é importado pelo Terraform no Key Vault (azurerm_key_vault_certificate.wildcard)
# e referenciado aqui via key_vault_secret_id. Requer web_rp access policy no KV.
resource "azurerm_app_service_certificate" "main" {
  count = var.enable_keyvault && var.pfx_file_path != "" && var.enable_custom_domain ? 1 : 0

  name                = "cert-${local.web_app_name}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  key_vault_secret_id = azurerm_key_vault_certificate.wildcard[0].versionless_secret_id

  tags = local.tags

  depends_on = [
    azurerm_key_vault_access_policy.web_rp,
    azurerm_key_vault_access_policy.app_service,
  ]
}

# --- SSL Binding (SNI) ---
resource "azurerm_app_service_certificate_binding" "main" {
  count = var.enable_keyvault && var.pfx_file_path != "" && var.enable_custom_domain ? 1 : 0

  hostname_binding_id = azurerm_app_service_custom_hostname_binding.main[0].id
  certificate_id      = azurerm_app_service_certificate.main[0].id
  ssl_state           = "SniEnabled"
}

# ============================================================
# Monitoring — Azure Monitor Alerts (custo: $0)
# ============================================================
# Alertas mínimos para garantir saúde do portal PcD.
# Notificações via e-mail para resposta rápida a incidentes.

# --- Action Group (destinatário dos alertas) ---
resource "azurerm_monitor_action_group" "email" {
  name                = "ag-nossodireito-email"
  resource_group_name = azurerm_resource_group.main.name
  short_name          = "nd-email"

  email_receiver {
    name                    = "admin"
    email_address           = var.alert_email
    use_common_alert_schema = true
  }

  tags = local.tags
}

# --- Alerta: HTTP 5xx (erros de servidor) ---
resource "azurerm_monitor_metric_alert" "http_5xx" {
  name                = "alert-${local.web_app_name}-5xx"
  resource_group_name = azurerm_resource_group.main.name
  scopes              = [azurerm_linux_web_app.main.id]
  description         = "Alerta quando há erros HTTP 5xx no App Service"
  severity            = 1
  frequency           = "PT5M"
  window_size         = "PT5M"
  auto_mitigate       = true

  criteria {
    metric_namespace = "Microsoft.Web/sites"
    metric_name      = "Http5xx"
    aggregation      = "Total"
    operator         = "GreaterThan"
    threshold        = 0
  }

  action {
    action_group_id = azurerm_monitor_action_group.email.id
  }

  tags = local.tags
}

# --- Alerta: Health Check Failures (disponibilidade) ---
resource "azurerm_monitor_metric_alert" "health_check" {
  name                = "alert-${local.web_app_name}-health"
  resource_group_name = azurerm_resource_group.main.name
  scopes              = [azurerm_linux_web_app.main.id]
  description         = "Alerta quando health check falha (site indisponível)"
  severity            = 0
  frequency           = "PT1M"
  window_size         = "PT5M"
  auto_mitigate       = true

  criteria {
    metric_namespace = "Microsoft.Web/sites"
    metric_name      = "HealthCheckStatus"
    aggregation      = "Average"
    operator         = "LessThan"
    threshold        = 100
  }

  action {
    action_group_id = azurerm_monitor_action_group.email.id
  }

  tags = local.tags
}

# --- Alerta: Response Time > 5s (performance degradada) ---
resource "azurerm_monitor_metric_alert" "response_time" {
  name                = "alert-${local.web_app_name}-latency"
  resource_group_name = azurerm_resource_group.main.name
  scopes              = [azurerm_linux_web_app.main.id]
  description         = "Alerta quando tempo de resposta médio excede 5 segundos"
  severity            = 2
  frequency           = "PT5M"
  window_size         = "PT15M"
  auto_mitigate       = true

  criteria {
    metric_namespace = "Microsoft.Web/sites"
    metric_name      = "HttpResponseTime"
    aggregation      = "Average"
    operator         = "GreaterThan"
    threshold        = 5
  }

  action {
    action_group_id = azurerm_monitor_action_group.email.id
  }

  tags = local.tags
}

# --- Alerta: HTTP 4xx excessivos (possível ataque/scan) ---
resource "azurerm_monitor_metric_alert" "http_4xx_spike" {
  name                = "alert-${local.web_app_name}-4xx"
  resource_group_name = azurerm_resource_group.main.name
  scopes              = [azurerm_linux_web_app.main.id]
  description         = "Alerta quando há mais de 50 erros 4xx em 5 minutos (possível scan/ataque)"
  severity            = 3
  frequency           = "PT5M"
  window_size         = "PT5M"
  auto_mitigate       = true

  criteria {
    metric_namespace = "Microsoft.Web/sites"
    metric_name      = "Http4xx"
    aggregation      = "Total"
    operator         = "GreaterThan"
    threshold        = 50
  }

  action {
    action_group_id = azurerm_monitor_action_group.email.id
  }

  tags = local.tags
}
