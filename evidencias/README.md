# Evidencias

Capturas que demuestran el funcionamiento end-to-end del proyecto. Coloca cada imagen en la subcarpeta
correspondiente, con nombre descriptivo (ej. `02-unity-catalog/catalogos-dev-prod.png`).

> Sugerencia: capturas en PNG, recortadas a lo relevante y con la URL/recurso visible para que se note el entorno real.

## Checklist por área

### 01 — Infraestructura Azure (`01-infra-azure/`)
- [ ] Resource Group `rg-fraud-detection` con sus recursos (vista del portal).
- [ ] Storage Account `stfraudasoto2026` → contenedores `raw`, `bronze`, `silver`, `golden`, `metastore`.
- [ ] Workspaces Databricks `dev` y `prod` (overview de cada uno).
- [ ] Access Connector `ac-fraud-uc` con rol **Storage Blob Data Contributor** sobre el Storage Account.

### 02 — Unity Catalog (`02-unity-catalog/`)
- [ ] Catálogos `catalog_dev` y `catalog_prod` en el explorador de Catalog.
- [ ] Storage credential `credential` y las external locations (`exlt-raw`, `exlt-bronze`, ...).
- [ ] Schemas del medallion (`bronze`, `silver`, `golden`, `ml`) dentro de un catálogo.

### 03 — ETL Medallion (`03-etl-medallion/`)
- [ ] Tabla `bronze` con datos (preview + conteo de filas).
- [ ] Tabla `silver` (limpieza + features) con preview.
- [ ] Tabla `golden` (analítica/agregados) con preview y conteo.

### 04 — ML / MLflow (`04-ml-mlflow/`)
- [ ] Experimento MLflow con runs (incluida la búsqueda de Hyperopt).
- [ ] Modelo `fraud_xgb` registrado en UC (`catalog_*.ml.fraud_xgb`) con alias **champion**.
- [ ] Métricas del champion (AUC-PR ~0.95, precision) y/o gráfico de feature importance (`es_noche` top).

### 05 — Model Serving (`05-model-serving/`)
- [ ] Endpoint `fraud-xgb-endpoint` en estado **Ready** (scale_to_zero).
- [ ] Prueba de inferencia: payload de entrada + respuesta del endpoint.

### 06 — Seguridad / Grants (`06-seguridad-grants/`)
- [ ] Grupos `analistas_fraude` e `ingenieros_datos` (admin console / Identity).
- [ ] Salida de `SHOW GRANTS ON CATALOG catalog_*` (o vista de permisos en Catalog).
- [ ] Log de la tarea `grants` del Job mostrando creación de grupos + grants aplicados.

### 07 — CI/CD GitHub Actions (`07-cicd-actions/`)
- [ ] Workflow **Deploy Databricks dev → prod** en verde (vista de la run).
- [ ] Job multi-task `WF_PROD_FRAUD_DETECTION` en prod con todas las tareas **Succeeded**
      (prepamb → ingest → transform → load → train → grants).

### 08 — Streamlit (`08-streamlit/`)
- [ ] App corriendo (`localhost:8501`) con el formulario de transacción.
- [ ] Una predicción: transacción de entrada + score/etiqueta de fraude devuelta por el endpoint.
