resource "azurerm_data_factory" "main" {
  name                = "adf-${local.name_prefix}-${var.unique_suffix}"
  resource_group_name = azurerm_resource_group.main.name
  location             = azurerm_resource_group.main.location

  identity {
    type = "SystemAssigned" 
  }

  tags = var.tags
}

resource "azurerm_key_vault_access_policy" "adf" {
  key_vault_id = azurerm_key_vault.main.id
  tenant_id    = data.azurerm_client_config.current.tenant_id
  object_id    = azurerm_data_factory.main.identity[0].principal_id

  secret_permissions = ["Get", "List"]
}

resource "azurerm_role_assignment" "adf_storage_contributor" {
  scope                = azurerm_storage_account.datalake.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id          = azurerm_data_factory.main.identity[0].principal_id
}
