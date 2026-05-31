# Resource Group raíz del proyecto.
resource "azurerm_resource_group" "rg" {
  name     = "rg-${var.prefix}-detection"
  location = var.location
  tags     = var.tags
}

# Storage Account ADLS Gen2 (Hierarchical Namespace habilitado) para la capa raw + medallion.
resource "azurerm_storage_account" "adls" {
  name                     = var.storage_account_name
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  account_kind             = "StorageV2"
  is_hns_enabled           = true # requerido para ADLS Gen2 / Unity Catalog

  # Acceso solo vía Managed Identity (sin claves compartidas para los datos).
  shared_access_key_enabled = true # necesario para que TF cree contenedores; el acceso de datos es vía MI

  tags = var.tags
}

# Contenedores: raw, bronze, silver, golden, metastore.
resource "azurerm_storage_container" "containers" {
  for_each           = toset(var.containers)
  name               = each.value
  storage_account_id = azurerm_storage_account.adls.id
}
