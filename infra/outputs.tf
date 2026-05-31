output "resource_group" {
  value = azurerm_resource_group.rg.name
}

output "storage_account" {
  value = azurerm_storage_account.adls.name
}

output "workspace_dev_url" {
  value = "https://${azurerm_databricks_workspace.dev.workspace_url}"
}

output "workspace_prod_url" {
  value = "https://${azurerm_databricks_workspace.prod.workspace_url}"
}

output "access_connector_principal_id" {
  value = azurerm_databricks_access_connector.ac.identity[0].principal_id
}

output "catalog_dev" {
  value = databricks_catalog.dev.name
}

output "catalog_prod" {
  value = databricks_catalog.prod.name
}

output "external_locations" {
  value = { for k, v in databricks_external_location.loc : k => v.url }
}
