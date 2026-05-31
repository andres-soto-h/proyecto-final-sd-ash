# Endpoint de Databricks Model Serving para el modelo de fraude.
# Se aplica DESPUÉS de entrenar y registrar el modelo (el modelo debe existir en UC).
# Habilitar con: terraform apply -var="enable_model_serving=true" -var="serving_model_version=N"

variable "enable_model_serving" {
  description = "Crear el endpoint de serving (requiere modelo ya registrado en UC)."
  type        = bool
  default     = false
}

variable "serving_model_version" {
  description = "Versión del modelo registrado a servir (alias champion suele ser la última)."
  type        = string
  default     = "1"
}

resource "databricks_model_serving" "fraud" {
  count    = var.enable_model_serving ? 1 : 0
  provider = databricks.prod
  name     = "fraud-xgb-endpoint"

  config {
    served_entities {
      name                  = "fraud-xgb"
      entity_name           = "${var.catalog_prod}.ml.fraud_xgb"
      entity_version        = var.serving_model_version
      workload_size         = "Small"
      scale_to_zero_enabled = true # controla costo: escala a 0 sin tráfico
    }

    traffic_config {
      routes {
        served_model_name  = "fraud-xgb"
        traffic_percentage = 100
      }
    }
  }

  depends_on = [databricks_catalog.prod]
}

output "serving_endpoint_url" {
  value       = var.enable_model_serving ? "${azurerm_databricks_workspace.prod.workspace_url}/serving-endpoints/fraud-xgb-endpoint/invocations" : null
  description = "URL de invocación del endpoint de serving (cuando está habilitado)."
}
