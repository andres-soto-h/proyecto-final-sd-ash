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

# Providers a NIVEL DE WORKSPACE. Se autentican con un token AAD (Bearer) inyectado por variable,
# generado con `az account get-access-token --resource 2ff814a6-3304-4ab8-85cb-cd0e6f879c1d`.
# Se evita la auth az-cli interna del provider (incompatible con versiones recientes de Azure CLI).
provider "databricks" {
  alias = "dev"
  host  = "https://${azurerm_databricks_workspace.dev.workspace_url}"
  token = var.databricks_aad_token
}

provider "databricks" {
  alias = "prod"
  host  = "https://${azurerm_databricks_workspace.prod.workspace_url}"
  token = var.databricks_aad_token
}
