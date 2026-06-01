# Workspace de Databricks — DEV (donde se desarrollan los notebooks).
resource "azurerm_databricks_workspace" "dev" {
  name                = "dbw-${var.prefix}-dev"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  sku                 = "premium" # premium requerido para Unity Catalog
  tags                = var.tags
}

# Workspace de Databricks — PROD (destino del CI/CD).
# depends_on fuerza creación secuencial: dos workspaces creándose en paralelo en la misma
# suscripción chocan en el role assignment del service principal de Databricks
# (error "ApplianceProvisioningFailed: The role assignment already exists").
resource "azurerm_databricks_workspace" "prod" {
  name                = "dbw-${var.prefix}-prod"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  sku                 = "premium"
  tags                = var.tags

  depends_on = [azurerm_databricks_workspace.dev]
}

# Access Connector for Azure Databricks = Managed Identity para acceder a ADLS.
resource "azurerm_databricks_access_connector" "ac" {
  name                = "ac-${var.prefix}-uc"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location

  identity {
    type = "SystemAssigned"
  }

  tags = var.tags
}

# RBAC: la Managed Identity del Access Connector lee/escribe el storage SIN claves ni SAS.
resource "azurerm_role_assignment" "ac_blob_contributor" {
  scope                = azurerm_storage_account.adls.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_databricks_access_connector.ac.identity[0].principal_id
}
