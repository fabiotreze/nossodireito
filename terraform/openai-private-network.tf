# ============================================================
# Private Networking — App Service <-> Azure OpenAI
# ============================================================
# Objetivo:
# - Eliminar tráfego público entre App Service e Azure OpenAI.
# - Forçar resolução privada via Private DNS Zone.
#
# Observação:
# - A integração VNet do App Service usa subnet delegada.
# - O Private Endpoint do OpenAI usa subnet dedicada.
# ============================================================

resource "azurerm_virtual_network" "private" {
  count = var.enable_openai_private_network ? 1 : 0

  name                = local.vnet_name
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  address_space       = var.vnet_address_space
  tags                = local.tags
}

resource "azurerm_subnet" "app_service_integration" {
  count = var.enable_openai_private_network ? 1 : 0

  name                 = local.appsvc_subnet_name
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.private[0].name
  address_prefixes     = [var.app_service_integration_subnet_cidr]

  delegation {
    name = "appservice-delegation"

    service_delegation {
      name = "Microsoft.Web/serverFarms"
      actions = [
        "Microsoft.Network/virtualNetworks/subnets/action",
      ]
    }
  }
}

resource "azurerm_subnet" "openai_private_endpoint" {
  count = var.enable_openai_private_network ? 1 : 0

  name                                      = local.openai_pe_subnet_name
  resource_group_name                       = azurerm_resource_group.main.name
  virtual_network_name                      = azurerm_virtual_network.private[0].name
  address_prefixes                          = [var.openai_private_endpoint_subnet_cidr]
  private_endpoint_network_policies = "Disabled"
}

resource "azurerm_private_dns_zone" "openai" {
  count = var.enable_openai_private_network ? 1 : 0

  name                = var.openai_private_dns_zone_name
  resource_group_name = azurerm_resource_group.main.name
  tags                = local.tags
}

resource "azurerm_private_dns_zone_virtual_network_link" "openai" {
  count = var.enable_openai_private_network ? 1 : 0

  name                  = "link-${local.vnet_name}-openai"
  resource_group_name   = azurerm_resource_group.main.name
  private_dns_zone_name = azurerm_private_dns_zone.openai[0].name
  virtual_network_id    = azurerm_virtual_network.private[0].id
  registration_enabled  = false
}

resource "azurerm_private_endpoint" "openai" {
  count = var.enable_openai_private_network && var.enable_ai_openai ? 1 : 0

  name                = "pe-${local.project}-openai${local.suffix}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  subnet_id           = azurerm_subnet.openai_private_endpoint[0].id
  tags                = local.tags

  private_service_connection {
    name                           = "psc-openai-${var.environment}"
    private_connection_resource_id = azurerm_cognitive_account.openai[0].id
    is_manual_connection           = false
    subresource_names              = ["account"]
  }

  private_dns_zone_group {
    name                 = "pdzg-openai"
    private_dns_zone_ids = [azurerm_private_dns_zone.openai[0].id]
  }
}
