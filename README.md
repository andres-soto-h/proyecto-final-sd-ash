# Proyecto Final — Detección de Fraude Bancario en Databricks

Trabajo final del curso **Ingeniería de Datos e IA con Databricks**. Implementa un pipeline ETL
**medallion** en Azure Databricks que alimenta un modelo de **detección de transacciones fraudulentas**
(XGBoost + MLflow), servido vía **Databricks Model Serving** y expuesto en una **web app de Streamlit**.
Toda la infraestructura se aprovisiona con **Terraform** y el despliegue dev→prod es automático con **GitHub Actions**.

## Arquitectura

```
                         Unity Catalog (metastore)
                                  │
  Kaggle (Sparkov)                │   Managed Identity (Access Connector)
  fraudTrain.csv  ──► ADLS raw ───┼──► BRONZE ──► SILVER ──► GOLDEN ──► XGBoost (MLflow/UC)
  fraudTest.csv       (Terraform) │   (ingest)   (transform)  (features)        │
                                  │                                     Model Serving endpoint
                                  │                                             │
                         Workspaces dev / prod                          Streamlit web app
                         (GitHub Actions dev→prod)
```

- **Capa raw**: contenedor ADLS Gen2, **fuera de DBFS/Volume**, leído **solo con Managed Identity**.
- **ETL**: PySpark DataFrame API (no `spark.sql` para transformaciones).
- **Medallion**: bronze (ingesta cruda) → silver (limpieza + features) → golden (tabla analítica + agregados).
- **ML**: XGBoost en pipeline sklearn, tracking MLflow, registro en Unity Catalog (alias `champion`).
- **Exposición**: endpoint de serving + app Streamlit.

## Estructura del repositorio

| Carpeta | Contenido |
|---------|-----------|
| `infra/` | Terraform: Azure + Unity Catalog + serving |
| `datasets/` | Enlaces a insumos + muestra (`sample_fraud.csv`); CSV reales van al contenedor raw |
| `prepAmb/` | Preparación de ambiente (schemas) |
| `proceso/` | Notebooks ETL PySpark + entrenamiento + creación de grupos y grants |
| `seguridad/` | `grants.sql` (espejo de los grants; los grupos los crea `5_grants.py` vía SDK) |
| `reversion/` | DROP de tablas/schemas y limpieza de rutas |
| `streamlit_app/` | Web app de exposición |
| `dashboard/` | Consultas SQL sobre `golden` + guía del tablero (`dashboard_queries.sql`) |
| `certificaciones/` | Certificaciones (png + enlaces) |
| `evidencias/` | Capturas de WF, Actions y recursos Azure |
| `.github/workflows/` | CI/CD dev→prod + Terraform CI |

> Nota: la rúbrica muestra la carpeta como `.github/workflow`; se usa `.github/workflows` (nombre que exige GitHub Actions).

## Puesta en marcha

### 1. Infraestructura (Terraform)
```bash
az login
cd infra
cp terraform.tfvars.example terraform.tfvars   # completar subscription/tenant/account id
terraform init && terraform apply
```
Crea RG, ADLS + contenedores, 2 workspaces, Access Connector + RBAC, metastore, storage credential,
external locations y catálogos. Ver `infra/README.md`.

### 2. Datasets
```bash
bash datasets/download_datasets.sh   # descarga Sparkov a datasets/raw/ (requiere Kaggle API)
# terraform apply sube fraudTrain.csv / fraudTest.csv al contenedor raw
```

### 3. Desarrollo en DEV
Importar `prepAmb/` y `proceso/` al workspace dev y ejecutar el pipeline completo:
`prepamb → ingest → transform → load → train → grants` (la última tarea crea los grupos `analistas_fraude`
e `ingenieros_datos` y aplica los permisos de Unity Catalog).

### 4. CI/CD dev → prod
Configurar **secrets** en GitHub (Settings → Secrets and variables → Actions):

| Secret | Descripción |
|--------|-------------|
| `DATABRICKS_ORIGIN_HOST` | URL workspace dev |
| `DATABRICKS_ORIGIN_TOKEN` | Token PAT dev |
| `DATABRICKS_ORIGIN_PATH` | Ruta de los notebooks en dev (ej. `/Workspace/Users/<you>/fraud_detection/proceso`) |
| `DATABRICKS_DEST_HOST` | URL workspace prod |
| `DATABRICKS_DEST_TOKEN` | Token PAT prod |

Un push a `main` que toque `proceso/**` dispara el workflow: exporta de dev, importa a prod, crea el Job
multi-task y lo ejecuta.

### 5. Model Serving + Streamlit
```bash
cd infra && terraform apply -var="enable_model_serving=true" -var="serving_model_version=<N>"
cd ../streamlit_app
cp .streamlit/secrets.toml.example .streamlit/secrets.toml   # completar host/endpoint/token
pip install -r requirements.txt
streamlit run app.py
```

## Decisiones de diseño
- **Terraform** crea infra Azure **y** objetos Unity Catalog (credential, external locations, catálogos);
  los notebooks `prepAmb` solo crean schemas.
- **Managed Identity** (Access Connector + Storage Credential) es la única vía de acceso a datos: sin keys ni SAS.
- **scale_to_zero** en el endpoint para controlar costos.

## Resultados
- **Modelo** `fraud_xgb` (XGBoost + Hyperopt, registrado en Unity Catalog con alias `champion`):
  **AUC-PR ≈ 0.95**, precision ≈ 0.68 sobre el conjunto de test. Features de mayor peso: `es_noche`,
  `amt_vs_avg_tarjeta`, `n_tx_ultimas_24h`.
- **Tablero** sobre la capa `golden` (`dashboard/`): tasa de fraude por categoría, hora, franja
  día/noche, fin de semana y rango de monto.
- **Endpoint** `fraud-xgb-endpoint` (scale_to_zero) sirviendo el champion, consumido por la app Streamlit.
- Evidencias del flujo end-to-end (infra, UC, ETL, ML, serving, grants, CI/CD, app) en `evidencias/`.

## Reversión / limpieza
- Tablas/schemas/rutas: notebook `reversion/drop_tablas.py`.
- Infraestructura completa: `terraform destroy` en `infra/`.

