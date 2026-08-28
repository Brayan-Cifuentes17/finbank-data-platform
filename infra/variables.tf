variable "project_name" {
  description = "Prefijo corto usado en el nombre de todos los recursos"
  type        = string
  default     = "finbank"
}

variable "environment" {
  description = "Entorno de despliegue: dev o pdn."
  type        = string
  validation {
    condition     = contains(["dev", "pdn"], var.environment)
    error_message = "El entorno debe ser 'dev' o 'pdn'."
  }
}

variable "location" {
  description = "Region de Azure donde se despliegan los recursos. "
  type        = string
  default     = "eastus"
}

variable "sql_server_location" {
  description = "Región especifica para el Azure SQL Server."
  type        = string
  default     = "eastus2"
}

variable "unique_suffix" {
  description = "Sufijo nombre"
  type        = string
}

variable "sql_admin_login" {
  description = "Usuario administrador del Azure SQL Server"
  type        = string
  default     = "finbankadmin"
}

variable "sql_admin_password" {
  description = "Password del administrador de Azure SQL Server."
  type        = string
  sensitive   = true
}

variable "client_ip_address" {
  description = "IP para la regla de firewall de Azure SQL "
  type        = string
}

variable "databricks_sku" {
  description = "SKU del workspace de Databricks."
  type        = string
  default     = "premium"
}

variable "budget_amount_usd" {
  description = "Controlar el gasto de la suscripcion"
  type        = number
  default     = 15
}

variable "alert_email" {
  description = "Correo cuando falle el pipeline."
  type        = string
}

variable "tags" {
  description = "Tags"
  type        = map(string)
  default = {
    proyecto  = "finbank-pipeline"
    origen    = "prueba-dataknow"
    escenario = "A"
  }
}
