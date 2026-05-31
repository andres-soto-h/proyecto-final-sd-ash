# Spec 00 — Overview del Proyecto

## Objetivo

Construir un sistema end-to-end de **detección de transacciones fraudulentas** sobre **Azure Databricks**,
cumpliendo los requisitos del trabajo final del curso (ETL medallion en PySpark, raw vía Managed Identity,
CI/CD dev→prod con GitHub Actions) y agregando valor con **Terraform** (IaC), **MLflow + XGBoost** (modelo) y
una **web app en Streamlit** (exposición).

## Alcance

| Incluye | No incluye |
|---------|-----------|
| Aprovisionamiento Azure + Unity Catalog con Terraform | Multi-región / alta disponibilidad |
| Medallion bronze/silver/golden en PySpark | Streaming en tiempo real (solo batch) |
| Modelo XGBoost + MLflow + Model Serving | Reentrenamiento automático programado |
| CI/CD dev→prod (notebooks + Job) | Tests unitarios exhaustivos de notebooks |
| App Streamlit que consume el endpoint | Autenticación de usuarios en la app |

## Requisitos de la rúbrica (trazabilidad)

| Requisito | Spec que lo cubre |
|-----------|-------------------|
| Arquitectura medallion | 03 |
| ETL en PySpark (DataFrame API, "no spark sql") | 03 |
| Raw fuera de DBFS/Volume, solo Managed Identity | 01, 02 |
| Mínimo 2 insumos (datasets) | 03 |
| CI/CD dev→prod con GitHub Actions (prepamb→extract→transform→load→grants) | 05 |
| Grants a usuarios/grupos | 02 |
| Reversión (DROP tablas y rutas) | 03 (notebook reversion) |
| Estructura de carpetas | este overview |
| Dashboard / visualización | 06 + dashboard/ |
| Documentación + arquitectura | README.md |

## Datasets (insumos)

- **Sparkov** `kartik2112/fraud-detection`: `fraudTrain.csv` + `fraudTest.csv` (2 insumos).
- Columnas relevantes: `trans_date_trans_time, cc_num, merchant, category, amt, gender, lat, long,
  city_pop, job, dob, merch_lat, merch_long, is_fraud`.
- Variable objetivo: `is_fraud` (0/1), fuertemente desbalanceada.

## Premisas operativas

- Commits **sin** `Co-Authored-By: Claude`.
- Raw **no** va directo a Databricks: se sube a contenedor ADLS y se lee con Storage Credential (Managed Identity).
- Repo **público** al entregar.

## Dependencias entre specs

```
01-infra  ──>  02-seguridad ──>  03-etl ──>  04-ml ──>  06-streamlit
                                   └──────────────────>  05-cicd (orquesta 03+04)
```
