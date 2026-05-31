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
terraform plan
terraform apply
```

## Orden lógico de dependencias
`RG → Storage/contenedores → Workspaces + Access Connector + RBAC → Metastore + assignment →
Storage Credential → External Locations → Catálogos → Upload datasets`.
Terraform resuelve el orden con los `depends_on` declarados.

## Notas
- `shared_access_key_enabled = true` se deja para que TF cree contenedores; el **acceso a datos** desde
  Databricks es exclusivamente vía Managed Identity (Storage Credential), nunca con claves/SAS.
- Para destruir: `terraform destroy` (apaga costos de workspaces y serving).
- State local por defecto; para state remoto descomentar el backend `azurerm` en `versions.tf`.
