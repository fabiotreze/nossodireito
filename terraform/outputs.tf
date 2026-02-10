# ============================================================
# Outputs
# ============================================================

output "environment" {
  description = "Ambiente atual"
  value       = var.environment
}

output "resource_group_name" {
  description = "Nome do Resource Group"
  value       = azurerm_resource_group.main.name
}

output "app_service_name" {
  description = "Nome do App Service"
  value       = azurerm_linux_web_app.main.name
}

output "app_service_plan" {
  description = "SKU do App Service Plan"
  value       = var.app_service_sku
}

output "default_hostname" {
  description = "Hostname padrão do Azure (usar como valor do CNAME no DNS)"
  value       = azurerm_linux_web_app.main.default_hostname
}

output "site_url" {
  description = "URL do site (Azure)"
  value       = "https://${azurerm_linux_web_app.main.default_hostname}"
}

output "custom_domain_url" {
  description = "URL com domínio customizado (se habilitado)"
  value       = var.enable_custom_domain && var.custom_domain != "" ? "https://${var.custom_domain}" : "(não configurado)"
}

output "dns_config" {
  description = "Configuração DNS para o seu provedor (GoDaddy, etc.)"
  value       = <<-EOT

    ┌──────────────────────────────────────────────────────────┐
    │  Configuração DNS                                        │
    ├──────────────────────────────────────────────────────────┤
    │  Type:  CNAME                                            │
    │  Name:  ${var.custom_domain != "" ? split(".", var.custom_domain)[0] : "<subdominio>"}
    │  Value: ${azurerm_linux_web_app.main.default_hostname}
    │  TTL:   600                                              │
    └──────────────────────────────────────────────────────────┘

    ⚠️  IMPORTANTE: O CNAME agora aponta para .azurewebsites.net
    (antes era .azurestaticapps.net). Atualize no GoDaddy!

  EOT
}

# --- Key Vault outputs ---
output "key_vault_name" {
  description = "Nome do Key Vault (se habilitado)"
  value       = var.enable_keyvault ? azurerm_key_vault.main[0].name : "(não habilitado)"
}

output "key_vault_uri" {
  description = "URI do Key Vault"
  value       = var.enable_keyvault ? azurerm_key_vault.main[0].vault_uri : "(não habilitado)"
}

output "certificate_name" {
  description = "Nome do certificado no Key Vault"
  value       = var.enable_keyvault && var.pfx_file_path != "" ? azurerm_key_vault_certificate.wildcard[0].name : "(não importado)"
}

output "ssl_state" {
  description = "Estado do SSL binding"
  value       = var.enable_keyvault && var.pfx_file_path != "" && var.enable_custom_domain ? "SNI Enabled (PFX via Key Vault)" : "Sem custom SSL"
}

# --- Application Insights ---
output "app_insights_name" {
  description = "Nome do Application Insights"
  value       = azurerm_application_insights.main.name
}

output "app_insights_instrumentation_key" {
  description = "Instrumentation Key (usar no SDK client-side se necessário)"
  value       = azurerm_application_insights.main.instrumentation_key
  sensitive   = true
}

output "app_insights_connection_string" {
  description = "Connection string do App Insights (injetada automaticamente no App Service)"
  value       = azurerm_application_insights.main.connection_string
  sensitive   = true
}

output "app_insights_portal_url" {
  description = "URL direta para o dashboard do App Insights no portal Azure"
  value       = "https://portal.azure.com/#@/resource${azurerm_application_insights.main.id}/overview"
}

output "next_steps" {
  description = "Próximos passos após terraform apply"
  value       = <<-EOT

    ┌──────────────────────────────────────────────────────────┐
    │  Próximos Passos                                         │
    ├──────────────────────────────────────────────────────────┤
    │  1. Atualize o CNAME no GoDaddy:                         │
    │     nossodireito → ${azurerm_linux_web_app.main.default_hostname}
    │                                                          │
    │  2. Dispare o deploy via GitHub Actions:                 │
    │     git push (auto-deploy no push para main)             │
    │                                                          │
    │  3. Verifique o SSL:                                     │
    │     curl -vI https://${var.custom_domain}                │
    └──────────────────────────────────────────────────────────┘

  EOT
}

# --- Monitoring Outputs ---
output "alert_email" {
  description = "E-mail que recebe alertas de monitoramento"
  value       = var.alert_email
}

output "monitoring_alerts" {
  description = "Alertas configurados"
  value = {
    http_5xx      = "Sev1 — Qualquer erro 5xx (imediato)"
    health_check  = "Sev0 — Health check < 100% (crítico)"
    response_time = "Sev2 — Latência média > 5s (15min)"
    http_4xx      = "Sev3 — Mais de 50 erros 4xx/5min (scan)"
  }
}
