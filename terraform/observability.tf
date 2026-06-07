# ============================================================
# Observability — Diagnostic Settings (App Service + KV + OpenAI)
# ============================================================
# Marco Civil da Internet (Lei 12.965/2014) — Art. 13 e 15:
#   provedor de aplicação deve guardar registros de acesso (logs)
#   por no mínimo 6 meses, em ambiente controlado e seguro.
#
# LGPD (Lei 13.709/2018) — Art. 16: o tratamento de dados pessoais
#   deve respeitar o princípio de prevenção e segurança.
#
# Estratégia: enviar logs do App Service, Key Vault e Azure OpenAI
# para o Log Analytics Workspace já existente (criado em main.tf),
# com retenção de 180 dias (≥ 6 meses) configurada no próprio workspace.
# ============================================================

# --- Retenção do workspace = 180 dias (Marco Civil) -----------------
#
# O recurso azurerm_log_analytics_workspace já existe em main.tf.
# A retenção é definida ali via var.log_analytics_retention_days (ver
# variables.tf). Este arquivo apenas adiciona os "sinks" — quem manda
# log pra esse workspace.

# --- App Service: HTTP logs + console + auditoria ------------------
resource "azurerm_monitor_diagnostic_setting" "app_service" {
  name                       = "diag-${local.web_app_name}"
  target_resource_id         = azurerm_linux_web_app.main.id
  log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id

  # AppServiceHTTPLogs = atende Marco Civil Art. 13 (IP + URL + timestamp).
  # AppServiceConsoleLogs = stdout/stderr do Node 22 (sem PII por design).
  # AppServiceAuditLogs = quem fez deploy / quem trocou config.
  # AppServiceAppLogs = logs de aplicação (server.js).
  # AppServiceIPSecAuditLogs = quem bypassou IP restriction (se houver).
  enabled_log { category = "AppServiceHTTPLogs" }
  enabled_log { category = "AppServiceConsoleLogs" }
  enabled_log { category = "AppServiceAppLogs" }
  enabled_log { category = "AppServiceAuditLogs" }
  enabled_log { category = "AppServiceIPSecAuditLogs" }
  enabled_log { category = "AppServicePlatformLogs" }

  enabled_metric { category = "AllMetrics" }
}

# --- Key Vault: auditoria de todo acesso a segredos ----------------
resource "azurerm_monitor_diagnostic_setting" "key_vault" {
  count = var.enable_keyvault ? 1 : 0

  name                       = "diag-${local.key_vault_name}"
  target_resource_id         = azurerm_key_vault.main[0].id
  log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id

  # AuditEvent = QUALQUER read/write em segredo / cert / chave.
  # Indispensável p/ provar acesso a PFX, openai-key, etc.
  enabled_log { category = "AuditEvent" }
  enabled_log { category = "AzurePolicyEvaluationDetails" }

  enabled_metric { category = "AllMetrics" }
}

# --- Azure OpenAI: requests, content filtering, deployment changes -
resource "azurerm_monitor_diagnostic_setting" "openai" {
  count = var.enable_ai_openai ? 1 : 0

  name                       = "diag-cog-${local.project}-openai${local.suffix}"
  target_resource_id         = azurerm_cognitive_account.openai[0].id
  log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id

  # Audit = mudanças em config (deployment, model swap).
  # RequestResponse = telemetria de requests (sem prompt/completion body).
  enabled_log { category = "Audit" }
  enabled_log { category = "RequestResponse" }

  enabled_metric { category = "AllMetrics" }
}
