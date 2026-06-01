# Infraestructura (Terraform)

Aprovisiona la infra Azure + objetos de Unity Catalog para el proyecto de detección de fraude.

## Recursos que crea
- Resource Group.
- Storage Account ADLS Gen2 (HNS) + contenedores `raw`, `bronze`, `silver`, `golden`, `metastore`.
- 2 workspaces de Databricks (`dev`, `prod`), SKU premium.
- Access Connector (Managed Identity) + rol `Storage Blob Data Contributor`.
- Unity Catalog: metastore + asignación a ambos workspaces, storage credential `credential`,
  external locations (`exlt-raw`, `exlt-bronze`, ...), catálogos `catalog_dev` / `catalog_prod`.
- Subida de `fraudTrain.csv` / `fraudTest.csv` al contenedor `raw`.

## Prerrequisitos
- Azure CLI autenticado: `az login` (rol Owner/Contributor en la suscripción).
- Permiso de **account admin** en Databricks (para crear el metastore).
- CSV de Kaggle descargados en `../datasets/raw/` (ver `datasets/README_datasets.txt`).

## Uso
```bash
cd infra
cp terraform.tfvars.example terraform.tfvars   # completar valores
terraform init
terraform validate
```

## Despliegue en dos etapas
Se despliega en dos etapas para evitar el chicken-and-egg del `account_id` y porque Azure
**auto-asigna un metastore por región** al crear el primer workspace (no hace falta crearlo).

**Etapa 1 — infra Azure** (no requiere `account_id`):
```bash
terraform apply \
  -target=azurerm_resource_group.rg \
  -target=azurerm_storage_account.adls \
  -target=azurerm_storage_container.containers \
  -target=azurerm_databricks_workspace.dev \
  -target=azurerm_databricks_workspace.prod \
  -target=azurerm_databricks_access_connector.ac \
  -target=azurerm_role_assignment.ac_blob_contributor
```

**Etapa 2 — objetos Unity Catalog** (workspace-level, auth vía `az login`):
```bash
terraform apply \
  -target=databricks_storage_credential.mi \
  -target=databricks_external_location.loc \
  -target=databricks_catalog.dev \
  -target=databricks_catalog.prod
```

**Datasets** (tras descargarlos en `../datasets/raw/`):
```bash
terraform apply   # aplica el resto, incluida la subida de CSV al contenedor raw
```

> Si tu región NO auto-asigna metastore, pon `create_metastore=true` y `databricks_account_id=<id>`
> (de https://accounts.azuredatabricks.net) antes de la Etapa 2.

## Notas
- Los workspaces se crean **secuencialmente** (`prod` depende de `dev`) para evitar el error
  `ApplianceProvisioningFailed: The role assignment already exists` al crearlos en paralelo.

## Notas
- `shared_access_key_enabled = true` se deja para que TF cree contenedores; el **acceso a datos** desde
  Databricks es exclusivamente vía Managed Identity (Storage Credential), nunca con claves/SAS.
- Para destruir: `terraform destroy` (apaga costos de workspaces y serving).
- State local por defecto; para state remoto descomentar el backend `azurerm` en `versions.tf`.
