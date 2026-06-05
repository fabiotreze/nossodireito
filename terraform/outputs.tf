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

output "next_steps" {
  description = "Configuração DNS e próximos passos após terraform apply"
  value       = <<-EOT

    ┌──────────────────────────────────────────────────────────┐
    │  Configuração DNS                                        │
    ├──────────────────────────────────────────────────────────┤
    │  Type:  CNAME                                            │
    │  Name:  ${var.custom_domain != "" ? split(".", var.custom_domain)[0] : "<subdominio>"}
    │  Value: ${azurerm_linux_web_app.main.default_hostname}
    │  TTL:   600                                              │
    ├──────────────────────────────────────────────────────────┤
    │  Próximos Passos                                         │
    ├──────────────────────────────────────────────────────────┤
    │  1. Atualize o CNAME na Cloudflare (proxied; veja acima)  │
    │  2. git push (auto-deploy no push para main)              │
    │  3. curl -vI https://${var.custom_domain}                │
    └──────────────────────────────────────────────────────────┘

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


# --- Monitoring Outputs ---
output "alert_email" {
  description = "E-mail que recebe alertas de monitoramento"
  value       = var.alert_email
}

output "openai_network_mode" {
  description = "Modo de rede do Azure OpenAI"
  value       = var.enable_openai_private_network ? "private_endpoint" : "public"
}

output "openai_private_endpoint_ip" {
  description = "IP privado atribuído ao Private Endpoint do OpenAI (se habilitado)"
  value       = var.enable_openai_private_network && var.enable_ai_openai ? azurerm_private_endpoint.openai[0].private_service_connection[0].private_ip_address : null
}

output "key_vault_private_endpoint_ip" {
  description = "IP privado atribuído ao Private Endpoint do Key Vault (se habilitado)"
  value       = var.enable_keyvault && var.enable_keyvault_private_network ? azurerm_private_endpoint.keyvault[0].private_service_connection[0].private_ip_address : null
}

output "redis_name" {
  description = "Nome do Azure Cache for Redis"
  value       = var.enable_redis ? azurerm_redis_cache.main[0].name : null
}

output "redis_hostname" {
  description = "Hostname do Azure Cache for Redis"
  value       = var.enable_redis ? azurerm_redis_cache.main[0].hostname : null
}

output "redis_private_endpoint_ip" {
  description = "IP privado atribuído ao Private Endpoint do Redis (se habilitado)"
  value       = var.enable_redis && var.enable_redis_private_network ? azurerm_private_endpoint.redis[0].private_service_connection[0].private_ip_address : null
}
