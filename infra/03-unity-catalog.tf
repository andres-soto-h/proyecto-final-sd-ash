# --- Metastore (OPCIONAL) ---
# En Azure normalmente se auto-crea y asigna un metastore por región al crear el 1er workspace.
# Solo crear/assignar si create_metastore=true (requiere databricks_account_id).
resource "databricks_metastore" "this" {
  count         = var.create_metastore ? 1 : 0
  provider      = databricks.account
  name          = "metastore-${var.prefix}-${var.location}"
  region        = var.location
  force_destroy = true
}

resource "databricks_metastore_assignment" "dev" {
  count        = var.create_metastore ? 1 : 0
  provider     = databricks.account
  metastore_id = databricks_metastore.this[0].id
  workspace_id = azurerm_databricks_workspace.dev.workspace_id
}

resource "databricks_metastore_assignment" "prod" {
  count        = var.create_metastore ? 1 : 0
  provider     = databricks.account
  metastore_id = databricks_metastore.this[0].id
  workspace_id = azurerm_databricks_workspace.prod.workspace_id
}

# --- Storage Credential (Managed Identity del Access Connector) ---
# Nivel de workspace: no requiere account_id. Requiere que el workspace tenga metastore asignado.
resource "databricks_storage_credential" "mi" {
  provider = databricks.dev
  name     = "credential"

  azure_managed_identity {
    access_connector_id = azurerm_databricks_access_connector.ac.id
  }

  comment    = "Managed Identity para acceder a ADLS (capa raw + medallion)."
  depends_on = [azurerm_role_assignment.ac_blob_contributor]
}

# --- External Locations (una por contenedor) ---
resource "databricks_external_location" "loc" {
  provider = databricks.dev
  for_each = toset(var.containers)

  name            = "exlt-${each.value}"
  url             = "abfss://${each.value}@${azurerm_storage_account.adls.name}.dfs.core.windows.net/"
  credential_name = databricks_storage_credential.mi.name
  comment         = "External location para el contenedor ${each.value}."

  depends_on = [databricks_storage_credential.mi]
}

# --- Catálogos por entorno ---
resource "databricks_catalog" "dev" {
  provider     = databricks.dev
  name         = var.catalog_dev
  storage_root = "abfss://metastore@${azurerm_storage_account.adls.name}.dfs.core.windows.net/"
  comment      = "Catálogo medallion del entorno DEV."
  properties   = { purpose = "fraud-detection-dev" }

  depends_on = [databricks_external_location.loc]
}

resource "databricks_catalog" "prod" {
  provider     = databricks.prod
  name         = var.catalog_prod
  storage_root = "abfss://metastore@${azurerm_storage_account.adls.name}.dfs.core.windows.net/"
  comment      = "Catálogo medallion del entorno PROD."
  properties   = { purpose = "fraud-detection-prod" }

  depends_on = [databricks_external_location.loc]
}
