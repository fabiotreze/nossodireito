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

output "static_web_app_name" {
  description = "Nome do Static Web App"
  value       = azurerm_static_web_app.main.name
}

output "sku" {
  description = "Tier do Static Web App"
  value       = var.sku_tier
}

output "default_hostname" {
  description = "Hostname padrão do Azure (usar como valor do CNAME no DNS)"
  value       = azurerm_static_web_app.main.default_host_name
}

output "api_key" {
  description = "API key para deploy (usar como AZURE_STATIC_WEB_APPS_API_TOKEN no GitHub Secrets)"
  value       = azurerm_static_web_app.main.api_key
  sensitive   = true
}

output "site_url" {
  description = "URL do site (Azure)"
  value       = "https://${azurerm_static_web_app.main.default_host_name}"
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
    │  Value: ${azurerm_static_web_app.main.default_host_name}
    │  TTL:   600                                              │
    └──────────────────────────────────────────────────────────┘

    Após configurar o CNAME, defina:
      enable_custom_domain = true
      custom_domain        = "${var.custom_domain}"
    E execute: terraform apply

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

output "next_steps" {
  description = "Próximos passos após terraform apply"
  value       = <<-EOT

    ┌──────────────────────────────────────────────────────────┐
    │  Próximos Passos                                         │
    ├──────────────────────────────────────────────────────────┤
    │  1. Copie api_key → GitHub Secrets:                      │
    │     terraform output -raw api_key                        │
    │     Secret name: AZURE_STATIC_WEB_APPS_API_TOKEN         │
    │                                                          │
    │  2. Configure CNAME no GoDaddy:                          │
    │     terraform output dns_config                          │
    │                                                          │
    │  3. Habilite domínio custom no tfvars:                   │
    │     enable_custom_domain = true                          │
    │     terraform apply                                      │
    │                                                          │
    │  4. git push → deploy automático via GitHub Actions      │
    └──────────────────────────────────────────────────────────┘

  EOT
}
