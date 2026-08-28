locals {
  name_prefix        = "${var.project_name}-${var.environment}"
  storage_name_clean = lower(replace("st${var.project_name}${var.environment}${var.unique_suffix}", "-", ""))
}

resource "azurerm_resource_group" "main" {
  name     = "rg-${local.name_prefix}"
  location = var.location
  tags     = var.tags
}

resource "azurerm_storage_account" "datalake" {
  name                     = local.storage_name_clean
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "LRS" 
  account_kind             = "StorageV2"
  is_hns_enabled           = true 

  tags = var.tags
}

resource "azurerm_storage_container" "bronze" {
  name                  = "bronze"
  storage_account_name  = azurerm_storage_account.datalake.name
  container_access_type = "private"
}

resource "azurerm_storage_container" "silver" {
  name                  = "silver"
  storage_account_name  = azurerm_storage_account.datalake.name
  container_access_type = "private"
}

resource "azurerm_storage_container" "gold" {
  name                  = "gold"
  storage_account_name  = azurerm_storage_account.datalake.name
  container_access_type = "private"
}
