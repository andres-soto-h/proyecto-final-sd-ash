# Databricks notebook source
# MAGIC %md
# MAGIC # 4. Entrenamiento del Modelo de Fraude (MLflow + XGBoost)
# MAGIC Entrena un `Pipeline(OrdinalEncoder + XGBClassifier)` sobre `golden.transactions_features`,
# MAGIC trackea con **MLflow**, registra en **Unity Catalog** y asigna el alias `champion`.
# MAGIC El pipeline encapsula la codificación → el endpoint recibe features crudas.

# COMMAND ----------

# MAGIC %pip install xgboost scikit-learn
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

dbutils.widgets.text("catalogo", "catalog_dev", "Catálogo")
dbutils.widgets.text("esquema", "golden", "Schema features")
dbutils.widgets.text("model_schema", "ml", "Schema del modelo")

catalogo     = dbutils.widgets.get("catalogo")
esquema      = dbutils.widgets.get("esquema")
model_schema = dbutils.widgets.get("model_schema")

model_name = f"{catalogo}.{model_schema}.fraud_xgb"

# COMMAND ----------

import mlflow
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OrdinalEncoder
from sklearn.pipeline import Pipeline
from sklearn.metrics import average_precision_score, recall_score, precision_score, f1_score, roc_auc_score
from xgboost import XGBClassifier

mlflow.set_registry_uri("databricks-uc")

# COMMAND ----------

pdf = spark.table(f"{catalogo}.{esquema}.transactions_features").toPandas()
print(f"Filas: {len(pdf)} | Tasa fraude: {pdf['is_fraud'].mean():.4f}")

cat_cols = ["category", "gender"]
num_cols = ["amt", "amt_log", "edad", "hora", "dia_semana", "dist_geo", "city_pop"]
features = cat_cols + num_cols

X = pdf[features]
y = pdf["is_fraud"].astype(int)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42)

# Manejo del desbalance.
neg, pos = (y_train == 0).sum(), (y_train == 1).sum()
scale_pos_weight = float(neg) / float(max(pos, 1))
print(f"scale_pos_weight = {scale_pos_weight:.2f}")

# COMMAND ----------

preprocessor = ColumnTransformer(
    transformers=[("cat", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1), cat_cols)],
    remainder="passthrough",
)

clf = XGBClassifier(
    n_estimators=300, max_depth=6, learning_rate=0.1,
    subsample=0.9, colsample_bytree=0.9,
    scale_pos_weight=scale_pos_weight, eval_metric="aucpr",
    n_jobs=-1, random_state=42,
)

pipe = Pipeline([("prep", preprocessor), ("xgb", clf)])

# COMMAND ----------

with mlflow.start_run(run_name="xgb_fraud") as run:
    pipe.fit(X_train, y_train)

    proba = pipe.predict_proba(X_test)[:, 1]
    preds = (proba >= 0.5).astype(int)
    metrics = {
        "auc_pr":    average_precision_score(y_test, proba),
        "roc_auc":   roc_auc_score(y_test, proba),
        "recall":    recall_score(y_test, preds),
        "precision": precision_score(y_test, preds, zero_division=0),
        "f1":        f1_score(y_test, preds),
    }
    mlflow.log_params({"n_estimators": 300, "max_depth": 6, "scale_pos_weight": scale_pos_weight})
    mlflow.log_metrics(metrics)
    print(metrics)

    signature = mlflow.models.infer_signature(X_test, preds)
    mlflow.sklearn.log_model(
        sk_model=pipe,
        artifact_path="model",
        signature=signature,
        input_example=X_test.head(3),
        registered_model_name=model_name,
    )

# COMMAND ----------

# Asignar alias champion a la última versión registrada.
from mlflow.tracking import MlflowClient

client = MlflowClient()
versions = client.search_model_versions(f"name='{model_name}'")
latest = max(versions, key=lambda v: int(v.version))
client.set_registered_model_alias(model_name, "champion", latest.version)
print(f"Modelo {model_name} v{latest.version} → alias 'champion'")
