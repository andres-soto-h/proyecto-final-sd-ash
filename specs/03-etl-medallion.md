# Spec 03 — ETL Medallion en PySpark

## Objetivo

Implementar el ETL medallion (bronze → silver → golden) en **PySpark con DataFrame API** (sin `spark.sql()` para
transformaciones; SQL solo para DDL de catálogo/schemas). Insumos: `fraudTrain.csv` y `fraudTest.csv` desde `raw`.

## Requisitos

1. Lectura de raw desde `abfss://raw@<sa>.dfs.core.windows.net/...` (Managed Identity).
2. Tablas Delta **externas** con `LOCATION 'abfss://<capa>@...'` (sin DBFS/Volume).
3. Parametrización por widgets: `catalogo`, `container`, `esquema`, `storageName`, `esquema_source`, `esquema_sink`.
4. Transformaciones con DataFrame API (`withColumn`, `join`, `groupBy`, funciones de `pyspark.sql.functions`).
5. Notebook de **reversión** que dropea tablas/schemas y limpia rutas físicas.

## Diseño

### Notebooks (`prepAmb/` y `proceso/`)
- `0_preparacion_ambiente` — crea schemas (`bronze/silver/golden`) y tablas Delta externas. (Storage credential,
  external locations y catálogo ya los crea Terraform — spec 01).
- `1_ingest_train` — lee `fraudTrain.csv` desde raw → `bronze.transactions_train` (+ `ingestion_date`).
- `1_ingest_test` — lee `fraudTest.csv` desde raw → `bronze.transactions_test`.
- `2_transform` — unifica train/test, casting de tipos, parse de fechas, deriva features base
  (`edad` desde `dob`, `hora`, `dia_semana`, `dist_geo` entre `lat/long` y `merch_lat/merch_long`),
  limpia nulos → `silver.transactions`.
- `3_load` — agregados y tabla analítica para el modelo/dashboard:
  `golden.transactions_features` (features finales) + `golden.fraud_by_category`, `golden.fraud_by_hour`.
- `5_grants` — ver spec 02.

### Esquema golden (features para ML)
`amt, category_idx, gender_idx, edad, hora, dia_semana, dist_geo, city_pop, amt_log, is_fraud`.

### Reversión (`reversion/drop_tablas.ipynb`)
- `DROP TABLE/SCHEMA ... CASCADE` + `dbutils.fs.rm("abfss://bronze@...", True)` para silver/golden.

## Tareas

1. `prepAmb/0_preparacion_ambiente.ipynb` (schemas + tablas).
2. Copia en `proceso/0_preparacion_ambiente.ipynb` (lo pide la rúbrica: prepamb también en proceso).
3. `proceso/1_ingest_train.ipynb`, `proceso/1_ingest_test.ipynb`.
4. `proceso/2_transform.ipynb` (DataFrame API).
5. `proceso/3_load.ipynb` (golden features + agregados).
6. `reversion/drop_tablas.ipynb`.

## Criterios de aceptación

- Tablas bronze/silver/golden creadas con conteos > 0.
- Transformaciones sin `spark.sql()` (solo DataFrame API).
- Reversión deja el entorno limpio.
