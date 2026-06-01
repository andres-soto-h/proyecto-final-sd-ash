variable "prefix" {
  description = "Prefijo para nombrar recursos (corto, sin caracteres especiales)."
  type        = string
  default     = "fraud"
}

variable "location" {
  description = "Región de Azure."
  type        = string
  default     = "eastus2"
}

variable "subscription_id" {
  description = "Azure Subscription ID."
  type        = string
}

variable "tenant_id" {
  description = "Azure Tenant ID."
  type        = string
}

variable "databricks_account_id" {
  description = "Databricks Account ID. Solo necesario si create_metastore=true."
  type        = string
  default     = ""
}

variable "databricks_aad_token" {
  description = "Token AAD (Bearer) para autenticar el provider de Databricks a nivel de workspace. Inyectar vía TF_VAR_databricks_aad_token con `az account get-access-token`."
  type        = string
  default     = ""
  sensitive   = true
}

variable "create_metastore" {
  description = "Crear y asignar el metastore de UC. En Azure normalmente se auto-crea con el 1er workspace; dejar en false y subirlo a true solo si no existe."
  type        = bool
  default     = false
}

variable "existing_metastore_id" {
  description = "ID de un metastore ya existente a asignar (opcional). Si vacío y create_metastore=false, se asume que el workspace ya tiene metastore asignado."
  type        = string
  default     = ""
}

variable "storage_account_name" {
  description = "Nombre global-único del Storage Account (3-24, minúsculas/números)."
  type        = string
  default     = "stfrauddetection01"
}

variable "containers" {
  description = "Contenedores ADLS Gen2 a crear."
  type        = list(string)
  default     = ["raw", "bronze", "silver", "golden", "metastore"]
}

variable "catalog_dev" {
  description = "Nombre del catálogo de Unity Catalog para dev."
  type        = string
  default     = "catalog_dev"
}

variable "catalog_prod" {
  description = "Nombre del catálogo de Unity Catalog para prod."
  type        = string
  default     = "catalog_prod"
}

variable "datasets_local_path" {
  description = "Ruta local a los CSV de Kaggle a subir al contenedor raw."
  type        = string
  default     = "../datasets/raw"
}

variable "tags" {
  description = "Tags comunes."
  type        = map(string)
  default = {
    project     = "fraud-detection"
    environment = "course-final"
    managed_by  = "terraform"
  }
}
