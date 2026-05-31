# Spec 01 — Infraestructura con Terraform (Azure + Unity Catalog)

## Objetivo

Aprovisionar con Terraform toda la infraestructura: recursos Azure (RG, ADLS Gen2, contenedores,
2 workspaces de Databricks, Access Connector) y objetos de Unity Catalog (storage credential,
external locations, catálogos dev/prod), de modo que el acceso a la capa raw sea **solo por Managed Identity**.

## Requisitos

1. Un **Resource Group** que agrupe todo.
2. **ADLS Gen2** (Storage Account con HNS habilitado) con contenedores: `raw`, `bronze`, `silver`, `golden`, `metastore`.
3. **Dos workspaces** de Azure Databricks: `dev` y `prod`.
4. **Access Connector for Azure Databricks** (Managed Identity) con rol **Storage Blob Data Contributor** sobre el storage.
5. **Unity Catalog**: asignación de metastore a cada workspace, **storage credential** (apuntando al Access Connector),
   **external locations** por contenedor, y catálogos `catalog_dev` / `catalog_prod`.
6. **Subida de datasets** al contenedor `raw` vía `azurerm_storage_blob` (los archivos NO se commitean).
7. Backend de state configurable (local por defecto; `azurerm` remoto opcional).
8. Sin secretos en el repo: `terraform.tfvars` ignorado; se entrega `terraform.tfvars.example`.

## Diseño

### Providers
- `azurerm` (autenticación vía `az login` / Service Principal con env vars `ARM_*`).
- `databricks` configurado a **nivel de cuenta** (host `https://accounts.azuredatabricks.net`, `account_id`) para metastore,
  y a **nivel de workspace** (alias por workspace) para storage credential / external locations / catálogos.

### Archivos
- `versions.tf` — required_providers + versión TF.
- `providers.tf` — azurerm + databricks (account + alias dev/prod).
- `variables.tf` — `prefix`, `location`, `tenant_id`, `subscription_id`, `databricks_account_id`,
  `storage_account_name`, nombres de catálogo, etc.
- `01-azure-base.tf` — RG, Storage Account (HNS), contenedores.
- `02-databricks-ws.tf` — 2 workspaces, Access Connector, `azurerm_role_assignment` (Storage Blob Data Contributor).
- `03-unity-catalog.tf` — `databricks_metastore_assignment`, `databricks_storage_credential`,
  `databricks_external_location` (raw/bronze/silver/golden/metastore), `databricks_catalog` dev/prod.
- `04-model-serving.tf` — endpoint de serving (ver spec 04; puede vivir aquí o aplicarse luego).
- `upload-datasets.tf` — `azurerm_storage_blob` para fraudTrain/fraudTest (path local configurable).
- `outputs.tf` — URLs de workspaces, nombre del storage, IDs de catálogos.

### Variables sensibles requeridas del usuario (se piden al hacer apply)
- `subscription_id`, `tenant_id`, `databricks_account_id`.
- Credenciales: `az login` interactivo o SP (`ARM_CLIENT_ID/SECRET/TENANT_ID/SUBSCRIPTION_ID`).

## Tareas

1. Escribir `versions.tf`, `providers.tf`, `variables.tf`, `outputs.tf`.
2. Escribir `01-azure-base.tf` (RG + storage + contenedores).
3. Escribir `02-databricks-ws.tf` (workspaces + access connector + RBAC).
4. Escribir `03-unity-catalog.tf` (metastore + credential + external locations + catálogos).
5. Escribir `upload-datasets.tf`.
6. `terraform.tfvars.example` + `infra/README.md` con orden de apply.
7. `terraform init && terraform validate` (sin credenciales aún → solo validate de sintaxis).

## Criterios de aceptación

- `terraform validate` pasa.
- `terraform plan` (con credenciales) muestra los recursos esperados sin errores.
- Tras `apply`: en Azure existen RG, storage con 5 contenedores, 2 workspaces, Access Connector con rol asignado.
- En Databricks: storage credential + 5 external locations + 2 catálogos visibles.
- Lectura de `abfss://raw@<sa>.dfs.core.windows.net/...` desde notebook **sin** keys/SAS (solo credential).
