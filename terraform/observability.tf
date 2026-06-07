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

# --- Redis: métricas do rate-limiter ------------------------------
# SKU Basic C0 NÃO suporta categorias de log (ConnectedClientList exige Premium).
# Para defesa-em-profundidade enviamos apenas métricas (CPU, conexões, ops/s,
# evictions, cache hits) ao Log Analytics — sem PII, sem payload de chave.
resource "azurerm_monitor_diagnostic_setting" "redis" {
  count = var.enable_redis ? 1 : 0

  name                       = "diag-${local.redis_name}"
  target_resource_id         = azurerm_redis_cache.main[0].id
  log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id

  enabled_metric { category = "AllMetrics" }
}

# ============================================================
# Security Alerts — KQL scheduled query rules
# ============================================================
# Defesa-em-profundidade. App Service já tem ip_restriction permitindo
# apenas faixas Cloudflare (ver main.tf), mas estes alertas servem como
# sinal antecipado de:
#   1. Bypass de Cloudflare (CIp fora das faixas conhecidas).
#   2. Acesso negado a Key Vault (forbidden / unauthorized).
# Sem custo adicional além de ingestion já incluído (PerGB2018 5GB grátis/mês).

# --- Alerta: Cloudflare bypass (origem direta no App Service) ------
resource "azurerm_monitor_scheduled_query_rules_alert_v2" "cloudflare_bypass" {
  count               = var.alert_email != "" ? 1 : 0
  name                = "alert-cloudflare-bypass"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location

  evaluation_frequency = "PT15M"
  window_duration      = "PT15M"
  scopes               = [azurerm_log_analytics_workspace.main.id]
  severity             = 2
  description          = "Requisição chegou ao App Service vinda de IP fora das faixas Cloudflare. Indica possível bypass do proxy reverso."

  criteria {
    query = <<-KQL
      let cf_ranges = dynamic(${jsonencode(local.cloudflare_ipv4_ranges)});
      AppServiceHTTPLogs
      | where TimeGenerated > ago(15m)
      | where isnotempty(CIp)
      | where not(ipv4_is_in_any_range(CIp, cf_ranges))
      | summarize hits = count(), sample_uri = any(CsUriStem) by CIp
      | where hits > 0
    KQL

    time_aggregation_method = "Count"
    operator                = "GreaterThan"
    threshold               = 0
  }

  auto_mitigation_enabled = true
  action {
    action_groups = [azurerm_monitor_action_group.email[0].id]
  }

  tags = local.tags
}

# --- Alerta: Key Vault — acesso negado / falha de autenticação -----
resource "azurerm_monitor_scheduled_query_rules_alert_v2" "kv_denied_access" {
  count               = var.enable_keyvault && var.alert_email != "" ? 1 : 0
  name                = "alert-kv-denied-access"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location

  evaluation_frequency = "PT15M"
  window_duration      = "PT1H"
  scopes               = [azurerm_log_analytics_workspace.main.id]
  severity             = 1
  description          = "Tentativas de acesso negadas (Forbidden/Unauthorized) ao Key Vault. Pode indicar credencial vazada ou identity drift."

  criteria {
    query = <<-KQL
      AzureDiagnostics
      | where TimeGenerated > ago(1h)
      | where ResourceProvider == "MICROSOFT.KEYVAULT"
      | where Category == "AuditEvent"
      | where ResultSignature in ("Forbidden", "Unauthorized")
      | summarize denials = count() by identity_claim_appid_g, CallerIPAddress
      | where denials > 0
    KQL

    time_aggregation_method = "Count"
    operator                = "GreaterThan"
    threshold               = 0
  }

  auto_mitigation_enabled = true
  action {
    action_groups = [azurerm_monitor_action_group.email[0].id]
  }

  tags = local.tags
}
