INSUMOS DEL PROYECTO (capa raw)
================================

Dataset: Credit Card Transactions Fraud Detection (Sparkov)
Autor: kartik2112
Enlace: https://www.kaggle.com/datasets/kartik2112/fraud-detection

Insumos (2, cumple el mínimo de la rúbrica):
  - fraudTrain.csv
  - fraudTest.csv

Columnas:
  index, trans_date_trans_time, cc_num, merchant, category, amt, first, last,
  gender, street, city, state, zip, lat, long, city_pop, job, dob, trans_num,
  unix_time, merch_lat, merch_long, is_fraud

Variable objetivo: is_fraud (0 = legítima, 1 = fraude). Dataset desbalanceado.

IMPORTANTE
----------
- Los CSV son grandes (~470MB train) y NO se commitean al repositorio.
- NO se cargan directo en Databricks (ni DBFS ni Volume).
- Se suben al contenedor `raw` del ADLS con Terraform (infra/upload-datasets.tf)
  y se leen desde Databricks vía Managed Identity (Storage Credential).

CÓMO OBTENERLOS
---------------
1. Configurar Kaggle API (https://www.kaggle.com/docs/api): colocar kaggle.json en ~/.kaggle/.
2. Ejecutar:  bash datasets/download_datasets.sh
   Esto descarga y descomprime los CSV en datasets/raw/ (carpeta ignorada por git).
3. Luego `terraform apply` en infra/ los sube al contenedor raw.

En este repo se incluye datasets/sample_fraud.csv (muestra pequeña, solo para inspección de esquema).
