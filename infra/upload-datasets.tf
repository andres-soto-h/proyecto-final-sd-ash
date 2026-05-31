# Sube los CSV de Kaggle al contenedor `raw` (NO van en Databricks ni se commitean al repo).
# Coloca los archivos en `datasets/raw/` (ver datasets/README_datasets.txt) antes de aplicar.
locals {
  raw_files = {
    "fraudTrain.csv" = "${var.datasets_local_path}/fraudTrain.csv"
    "fraudTest.csv"  = "${var.datasets_local_path}/fraudTest.csv"
  }
}

resource "azurerm_storage_blob" "raw_datasets" {
  for_each = local.raw_files

  name                   = each.key
  storage_account_name   = azurerm_storage_account.adls.name
  storage_container_name = azurerm_storage_container.containers["raw"].name
  type                   = "Block"
  source                 = each.value
}
