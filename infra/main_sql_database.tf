resource "azurerm_mssql_server" "main" {
  name                         = "sql-${local.name_prefix}-v1"
  resource_group_name         = azurerm_resource_group.main.name
  location                    = var.sql_server_location 
  version                     = "12.0"
  administrator_login         = var.sql_admin_login
  administrator_login_password = var.sql_admin_password
  minimum_tls_version          = "1.2"

  tags = var.tags
}

resource "azurerm_mssql_database" "finbank" {
  name        = "sqldb-finbank-source"
  server_id   = azurerm_mssql_server.main.id
  collation   = "SQL_Latin1_General_CP1_CI_AS"
  sku_name    = "GP_S_Gen5_1"
  min_capacity = 0.5 
  auto_pause_delay_in_minutes = 60 

  tags = var.tags
}

resource "azurerm_mssql_firewall_rule" "allow_azure_services" {
  name             = "AllowAzureServices"
  server_id        = azurerm_mssql_server.main.id
  start_ip_address = "0.0.0.0"
  end_ip_address   = "0.0.0.0"
}

resource "azurerm_mssql_firewall_rule" "allow_client_ip" {
  name             = "AllowClientIP"
  server_id        = azurerm_mssql_server.main.id
  start_ip_address = var.client_ip_address
  end_ip_address   = var.client_ip_address
}
