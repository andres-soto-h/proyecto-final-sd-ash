provider "azurerm" {
  features {}

  subscription_id = var.subscription_id
  tenant_id       = var.tenant_id
}

# Provider de Databricks a NIVEL DE CUENTA (para metastore y asignaciones).
provider "databricks" {
  alias      = "account"
  host       = "https://accounts.azuredatabricks.net"
  account_id = var.databricks_account_id
  # Autenticación: az CLI (az login) o variables DATABRICKS_* / ARM_*.
}

# Provider a NIVEL DE WORKSPACE DEV. Autenticación vía Azure CLI (az login).
provider "databricks" {
  alias                       = "dev"
  host                        = "https://${azurerm_databricks_workspace.dev.workspace_url}"
  azure_workspace_resource_id = azurerm_databricks_workspace.dev.id
}

# Provider a NIVEL DE WORKSPACE PROD.
provider "databricks" {
  alias                       = "prod"
  host                        = "https://${azurerm_databricks_workspace.prod.workspace_url}"
  azure_workspace_resource_id = azurerm_databricks_workspace.prod.id
}
