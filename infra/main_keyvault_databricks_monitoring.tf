data "azurerm_client_config" "current" {}

resource "azurerm_key_vault" "main" {
  name                       = "kv-${var.project_name}-${var.environment}-${var.unique_suffix}"
  resource_group_name       = azurerm_resource_group.main.name
  location                  = azurerm_resource_group.main.location
  tenant_id                 = data.azurerm_client_config.current.tenant_id
  sku_name                   = "standard"
  soft_delete_retention_days = 7
  purge_protection_enabled   = false 

  tags = var.tags
}

resource "azurerm_key_vault_access_policy" "deployer" {
  key_vault_id = azurerm_key_vault.main.id
  tenant_id    = data.azurerm_client_config.current.tenant_id
  object_id    = data.azurerm_client_config.current.object_id

  secret_permissions = ["Get", "List", "Set", "Delete", "Purge"]
}

resource "azurerm_key_vault_secret" "sql_connection_string" {
  name         = "sql-connection-string"
  value        = "Server=tcp:${azurerm_mssql_server.main.fully_qualified_domain_name},1433;Database=${azurerm_mssql_database.finbank.name};User ID=${var.sql_admin_login};Password=${var.sql_admin_password};Encrypt=true;"
  key_vault_id = azurerm_key_vault.main.id

  depends_on = [azurerm_key_vault_access_policy.deployer]
}

resource "azurerm_key_vault_secret" "storage_connection_string" {
  name         = "storage-connection-string"
  value        = azurerm_storage_account.datalake.primary_connection_string
  key_vault_id = azurerm_key_vault.main.id

  depends_on = [azurerm_key_vault_access_policy.deployer]
}


resource "azurerm_databricks_workspace" "main" {
  name                = "dbw-${local.name_prefix}"
  resource_group_name = azurerm_resource_group.main.name
  location             = azurerm_resource_group.main.location
  sku                  = var.databricks_sku

  tags = var.tags
}

resource "azurerm_log_analytics_workspace" "main" {
  name                = "log-${local.name_prefix}"
  resource_group_name = azurerm_resource_group.main.name
  location             = azurerm_resource_group.main.location
  sku                  = "PerGB2018"
  retention_in_days     = 30

  tags = var.tags
}

resource "azurerm_monitor_action_group" "pipeline_alerts" {
  name                = "ag-${local.name_prefix}-alerts"
  resource_group_name = azurerm_resource_group.main.name
  short_name          = "finbankalr"

  email_receiver {
    name          = "Brayan"
    email_address = var.alert_email
  }

  tags = var.tags
}

resource "azurerm_consumption_budget_resource_group" "main" {
  name              = "budget-${local.name_prefix}"
  resource_group_id = azurerm_resource_group.main.id

  amount     = var.budget_amount_usd
  time_grain = "Monthly"

  time_period {
    start_date = "2026-08-01T00:00:00Z"
    end_date   = "2027-08-01T00:00:00Z"
  }

  notification {
    enabled        = true
    threshold      = 50
    operator       = "GreaterThan"
    contact_emails = [var.alert_email]
  }

  notification {
    enabled        = true
    threshold      = 80
    operator       = "GreaterThan"
    contact_emails = [var.alert_email]
  }
}
