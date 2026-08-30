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

resource "azurerm_data_factory_trigger_schedule" "diario" {
  name            = "trg-${local.name_prefix}"
  data_factory_id = azurerm_data_factory.main.id
  pipeline_name   = "pl_finbank_master"

  interval  = 1
  frequency = "Day"

  schedule {
    hours   = [2]
    minutes = [0]
  }
  time_zone = "SA Pacific Standard Time"

  pipeline_parameters = {
    filtro_tabla  = ""
    run_full_load = "false"
  }
  activated = false
}

resource "azurerm_monitor_diagnostic_setting" "adf_diagnostics" {
  name                       = "diag-${local.name_prefix}-adf"
  target_resource_id         = azurerm_data_factory.main.id
  log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id
  log_analytics_destination_type = "Dedicated"  

  enabled_log {
    category = "ActivityRuns"
  }

  enabled_log {
    category = "PipelineRuns"
  }
}

resource "azurerm_monitor_scheduled_query_rules_alert_v2" "adf_activity_failed" {
  name                = "alert-${local.name_prefix}-activity-failed"
  resource_group_name = azurerm_resource_group.main.name
  location             = azurerm_resource_group.main.location
  evaluation_frequency  = "PT5M"   
  window_duration       = "PT15M" 
  scopes                = [azurerm_log_analytics_workspace.main.id]
  severity              = 1
  criteria {
    query = <<-QUERY
      ADFActivityRun
      | where Status == "Failed"
      | project
          Pipeline = PipelineName,
          Tarea = ActivityName,
          Error = tostring(Error),
          Hora_Fallo_UTC = End
      | order by Hora_Fallo_UTC desc
    QUERY
    time_aggregation_method = "Count"
    threshold                = 0
    operator                 = "GreaterThan"
  }

  action {
    action_groups = [azurerm_monitor_action_group.pipeline_alerts.id]
  }

  auto_mitigation_enabled = false
  description               = "se ejecuta cuando una actividad de ADF falla."
  tags                       = var.tags

  depends_on = [azurerm_monitor_diagnostic_setting.adf_diagnostics]
}
