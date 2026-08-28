output "resource_group_name" {
  value = azurerm_resource_group.main.name
}

output "storage_account_name" {
  value = azurerm_storage_account.datalake.name
}

output "storage_account_dfs_endpoint" {
  description = "Endpoint ADLS Gen2"
  value       = azurerm_storage_account.datalake.primary_dfs_endpoint
}

output "sql_server_fqdn" {
  description = "Nombre completo del servidor SQL"
  value       = azurerm_mssql_server.main.fully_qualified_domain_name
}

output "sql_database_name" {
  value = azurerm_mssql_database.finbank.name
}

output "databricks_workspace_url" {
  value = azurerm_databricks_workspace.main.workspace_url
}

output "data_factory_name" {
  value = azurerm_data_factory.main.name
}

output "key_vault_name" {
  value = azurerm_key_vault.main.name
}

output "key_vault_uri" {
  value = azurerm_key_vault.main.vault_uri
}

output "log_analytics_workspace_id" {
  value = azurerm_log_analytics_workspace.main.workspace_id
}
