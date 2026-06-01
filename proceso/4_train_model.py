# Databricks notebook source
# MAGIC %md
# MAGIC # 4. Entrenamiento del Modelo de Fraude (MLflow + XGBoost + Hyperopt)
# MAGIC Optimiza hiperparámetros con **Hyperopt (TPE)** maximizando **AUC-PR** por validación cruzada,
# MAGIC trackea cada trial en **MLflow**, entrena el modelo final con los mejores parámetros, lo registra
# MAGIC en **Unity Catalog** y fija el alias `champion`. Pipeline `OrdinalEncoder + XGBClassifier`
# MAGIC (el endpoint recibe features crudas).

# COMMAND ----------

# MAGIC %pip install xgboost scikit-learn hyperopt
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

dbutils.widgets.text("catalogo", "catalog_dev", "Catálogo")
dbutils.widgets.text("esquema", "golden", "Schema features")
dbutils.widgets.text("model_schema", "ml", "Schema del modelo")
dbutils.widgets.text("max_evals", "20", "Trials de Hyperopt")

catalogo     = dbutils.widgets.get("catalogo")
esquema      = dbutils.widgets.get("esquema")
model_schema = dbutils.widgets.get("model_schema")
max_evals    = int(dbutils.widgets.get("max_evals"))

model_name = f"{catalogo}.{model_schema}.fraud_xgb"

# COMMAND ----------

import mlflow
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OrdinalEncoder
from sklearn.pipeline import Pipeline
from sklearn.metrics import average_precision_score, recall_score, precision_score, f1_score, roc_auc_score
from xgboost import XGBClassifier
from hyperopt import fmin, tpe, hp, Trials, STATUS_OK

mlflow.set_registry_uri("databricks-uc")

# COMMAND ----------

pdf = spark.table(f"{catalogo}.{esquema}.transactions_features").toPandas()
print(f"Filas: {len(pdf)} | Tasa fraude: {pdf['is_fraud'].mean():.4f}")

cat_cols = ["category", "gender"]
num_cols = ["amt", "amt_log", "edad", "hora", "dia_semana", "es_noche", "es_fin_semana",
            "dist_geo", "city_pop", "tiempo_desde_ultima_tx_seg", "n_tx_ultimas_24h", "amt_vs_avg_tarjeta"]
features = cat_cols + num_cols

X = pdf[features]
y = pdf["is_fraud"].astype(int)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42)

neg, pos = (y_train == 0).sum(), (y_train == 1).sum()
scale_pos_weight = float(neg) / float(max(pos, 1))
print(f"scale_pos_weight = {scale_pos_weight:.2f}")

# Submuestra estratificada para acelerar la búsqueda de hiperparámetros.
X_hpo, _, y_hpo, _ = train_test_split(X_train, y_train, train_size=min(150000, len(X_train)),
                                      stratify=y_train, random_state=42)

# COMMAND ----------

def make_pipeline(params):
    pre = ColumnTransformer(
        [("cat", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1), cat_cols)],
        remainder="passthrough")
    clf = XGBClassifier(
        n_estimators=int(params["n_estimators"]),
        max_depth=int(params["max_depth"]),
        learning_rate=params["learning_rate"],
        subsample=params["subsample"],
        colsample_bytree=params["colsample_bytree"],
        min_child_weight=int(params["min_child_weight"]),
        gamma=params["gamma"],
        scale_pos_weight=scale_pos_weight,
        eval_metric="aucpr", n_jobs=-1, random_state=42)
    return Pipeline([("prep", pre), ("xgb", clf)])

# COMMAND ----------

# MAGIC %md ## Búsqueda de hiperparámetros con Hyperopt (TPE)

# COMMAND ----------

space = {
    "n_estimators":     hp.quniform("n_estimators", 150, 500, 50),
    "max_depth":        hp.quniform("max_depth", 3, 10, 1),
    "learning_rate":    hp.loguniform("learning_rate", np.log(0.01), np.log(0.3)),
    "subsample":        hp.uniform("subsample", 0.6, 1.0),
    "colsample_bytree": hp.uniform("colsample_bytree", 0.6, 1.0),
    "min_child_weight": hp.quniform("min_child_weight", 1, 10, 1),
    "gamma":            hp.uniform("gamma", 0.0, 5.0),
}
cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)

def objective(params):
    with mlflow.start_run(nested=True):
        pipe = make_pipeline(params)
        score = cross_val_score(pipe, X_hpo, y_hpo, cv=cv, scoring="average_precision", n_jobs=-1).mean()
        mlflow.log_params({k: (int(v) if k in ("n_estimators", "max_depth", "min_child_weight") else v)
                           for k, v in params.items()})
        mlflow.log_metric("cv_auc_pr", score)
        return {"loss": -score, "status": STATUS_OK}

with mlflow.start_run(run_name="hyperopt_search") as parent:
    trials = Trials()
    best = fmin(objective, space, algo=tpe.suggest, max_evals=max_evals, trials=trials)
    print("Mejores hiperparámetros:", best)

# COMMAND ----------

# MAGIC %md ## Modelo final con los mejores hiperparámetros

# COMMAND ----------

best_params = {
    "n_estimators":     best["n_estimators"],
    "max_depth":        best["max_depth"],
    "learning_rate":    best["learning_rate"],
    "subsample":        best["subsample"],
    "colsample_bytree": best["colsample_bytree"],
    "min_child_weight": best["min_child_weight"],
    "gamma":            best["gamma"],
}

with mlflow.start_run(run_name="xgb_fraud_final") as run:
    pipe = make_pipeline(best_params)
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
    mlflow.log_params({k: (int(v) if k in ("n_estimators", "max_depth", "min_child_weight") else v)
                       for k, v in best_params.items()})
    mlflow.log_metrics(metrics)
    print("Métricas finales:", metrics)

    # Importancia de features (sobre nombres post-encoding).
    importances = pipe.named_steps["xgb"].feature_importances_
    fi = pd.DataFrame({"feature": cat_cols + num_cols, "importance": importances}) \
           .sort_values("importance", ascending=False)
    fi.to_csv("/tmp/feature_importance.csv", index=False)
    mlflow.log_artifact("/tmp/feature_importance.csv")
    print(fi.to_string(index=False))

    signature = mlflow.models.infer_signature(X_test, preds)
    mlflow.sklearn.log_model(
        sk_model=pipe, artifact_path="model", signature=signature,
        input_example=X_test.head(3), registered_model_name=model_name)

# COMMAND ----------

# Fijar alias champion a la última versión registrada.
from mlflow.tracking import MlflowClient

client = MlflowClient(registry_uri="databricks-uc")
versions = client.search_model_versions(f"name='{model_name}'")
latest = max(versions, key=lambda v: int(v.version))
client.set_registered_model_alias(model_name, "champion", latest.version)
print(f"Modelo {model_name} v{latest.version} → alias 'champion'")
