# Spec 04 — Modelo de Detección de Fraude (MLflow + XGBoost + Serving)

## Objetivo

Entrenar un clasificador **XGBoost** sobre la tabla golden, trackear el experimento con **MLflow**,
registrar el modelo en **Unity Catalog** y servirlo con un endpoint de **Databricks Model Serving**
que la app Streamlit consume.

## Requisitos

1. Entrenamiento sobre `catalog.golden.transactions_features`.
2. Tracking con MLflow: params, métricas y artefactos (modelo + matriz de confusión).
3. Manejo del **desbalance** (is_fraud raro): `scale_pos_weight` y métricas adecuadas (**AUC-PR**, recall, F1), no solo accuracy.
4. Registro en UC: `catalog.ml.fraud_xgb` con alias `champion`.
5. Endpoint de **Model Serving** sirviendo la última versión `champion`.

## Diseño

### Notebook `proceso/4_train_model.ipynb`
- Carga golden como Pandas (o Spark→Pandas para XGBoost local) — dataset cabe en memoria del driver.
- Split train/test estratificado.
- `mlflow.set_registry_uri("databricks-uc")`; `with mlflow.start_run():`
  - entrena `xgboost.XGBClassifier(scale_pos_weight=ratio, eval_metric="aucpr", ...)`.
  - `mlflow.log_metrics({auc_pr, recall, precision, f1})`.
  - `mlflow.xgboost.log_model(model, "model", registered_model_name="<catalog>.ml.fraud_xgb")`.
- Setea alias `champion` a la nueva versión vía `MlflowClient`.

### Serving (`infra/04-model-serving.tf`)
- `databricks_model_serving` con `served_entities` apuntando a `catalog.ml.fraud_xgb@champion`,
  `workload_size = "Small"`, `scale_to_zero_enabled = true` (controla costo).
- Alternativa por API en el workflow si TF no aplica el endpoint en prod.

### Schema de inferencia
Input JSON (una transacción) con las features de golden; output: `{prediction, probability}`.

## Tareas

1. Crear schema `ml` en prepAmb (o en el notebook de train).
2. `proceso/4_train_model.ipynb` (entrenamiento + MLflow + registro + alias).
3. `infra/04-model-serving.tf` (endpoint, scale-to-zero).
4. Documentar firma de entrada/salida para Streamlit.

## Criterios de aceptación

- Run visible en MLflow con AUC-PR razonable (> baseline de clase mayoritaria).
- Modelo versión N registrado en UC con alias `champion`.
- Endpoint `READY`; `curl` con un payload devuelve `{prediction, probability}`.
