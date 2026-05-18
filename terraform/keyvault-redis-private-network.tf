# ============================================================
# Private Networking — Key Vault + Redis
# ============================================================
# Objetivo:
# - Isolar o Key Vault via Private Endpoint e DNS privado.
# - Provisionar Azure Cache for Redis Basic C0 com Private Endpoint.
# - Reutilizar a VNet já criada para o App Service e OpenAI.
# ============================================================

resource "azurerm_subnet" "keyvault_private_endpoint" {
  count = var.enable_keyvault && var.enable_keyvault_private_network ? 1 : 0

  name                 = local.keyvault_pe_subnet_name
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.private[0].name
  address_prefixes     = [var.keyvault_private_endpoint_subnet_cidr]

  private_endpoint_network_policies = "Disabled"
}

resource "azurerm_private_dns_zone" "keyvault" {
  count = var.enable_keyvault && var.enable_keyvault_private_network ? 1 : 0

  name                = var.keyvault_private_dns_zone_name
  resource_group_name = azurerm_resource_group.main.name
  tags                = local.tags
}

resource "azurerm_private_dns_zone_virtual_network_link" "keyvault" {
  count = var.enable_keyvault && var.enable_keyvault_private_network ? 1 : 0

  name                  = "vnetlink-kv-${var.environment}"
  resource_group_name   = azurerm_resource_group.main.name
  private_dns_zone_name = azurerm_private_dns_zone.keyvault[0].name
  virtual_network_id    = azurerm_virtual_network.private[0].id
  registration_enabled  = false
}

resource "azurerm_private_endpoint" "keyvault" {
  count = var.enable_keyvault && var.enable_keyvault_private_network ? 1 : 0

  name                = "pe-kv-${local.project}${local.suffix}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  subnet_id           = azurerm_subnet.keyvault_private_endpoint[0].id

  private_service_connection {
    name                           = "psc-kv-${local.project}${local.suffix}"
    private_connection_resource_id = azurerm_key_vault.main[0].id
    is_manual_connection           = false
    subresource_names              = ["vault"]
  }

  private_dns_zone_group {
    name                 = "pdzg-kv"
    private_dns_zone_ids = [azurerm_private_dns_zone.keyvault[0].id]
  }
}

resource "azurerm_redis_cache" "main" {
  count = var.enable_redis ? 1 : 0

  name                = local.redis_name
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name

  capacity = var.redis_capacity
  family   = var.redis_family
  sku_name = var.redis_sku_name

  minimum_tls_version           = "1.2"
  non_ssl_port_enabled          = false
  public_network_access_enabled = false

  tags = merge(local.tags, {
    "DataResidency" = "brazil-south"
    "Purpose"       = "rate-limiter-cache"
  })
}

resource "azurerm_key_vault_secret" "redis_primary_key" {
  count = var.enable_redis && var.manage_redis_secret_with_terraform ? 1 : 0

  name         = "redis-primary-key"
  value        = azurerm_redis_cache.main[0].primary_access_key
  key_vault_id = azurerm_key_vault.main[0].id

  depends_on = [azurerm_key_vault_access_policy.deployer]
}

locals {
  redis_app_settings = var.enable_redis ? {
    REDIS_RATE_LIMIT_ENABLED = "true"
    REDIS_HOSTNAME           = azurerm_redis_cache.main[0].hostname
    REDIS_PORT               = "6380"
    REDIS_SECRET_NAME        = "redis-primary-key"
    KEY_VAULT_URI            = azurerm_key_vault.main[0].vault_uri
  } : {}
}

resource "azurerm_subnet" "redis_private_endpoint" {
  count = var.enable_redis && var.enable_redis_private_network ? 1 : 0

  name                 = local.redis_pe_subnet_name
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.private[0].name
  address_prefixes     = [var.redis_private_endpoint_subnet_cidr]

  private_endpoint_network_policies = "Disabled"
}

resource "azurerm_private_dns_zone" "redis" {
  count = var.enable_redis && var.enable_redis_private_network ? 1 : 0

  name                = var.redis_private_dns_zone_name
  resource_group_name = azurerm_resource_group.main.name
  tags                = local.tags
}

resource "azurerm_private_dns_zone_virtual_network_link" "redis" {
  count = var.enable_redis && var.enable_redis_private_network ? 1 : 0

  name                  = "vnetlink-redis-${var.environment}"
  resource_group_name   = azurerm_resource_group.main.name
  private_dns_zone_name = azurerm_private_dns_zone.redis[0].name
  virtual_network_id    = azurerm_virtual_network.private[0].id
  registration_enabled  = false
}

resource "azurerm_private_endpoint" "redis" {
  count = var.enable_redis && var.enable_redis_private_network ? 1 : 0

  name                = "pe-redis-${local.project}${local.suffix}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  subnet_id           = azurerm_subnet.redis_private_endpoint[0].id

  private_service_connection {
    name                           = "psc-redis-${local.project}${local.suffix}"
    private_connection_resource_id = azurerm_redis_cache.main[0].id
    is_manual_connection           = false
    subresource_names              = ["redisCache"]
  }

  private_dns_zone_group {
    name                 = "pdzg-redis"
    private_dns_zone_ids = [azurerm_private_dns_zone.redis[0].id]
  }
}