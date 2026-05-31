# Databricks notebook source
# MAGIC %md
# MAGIC # 3. Load (Silver → Golden)
# MAGIC Construye la tabla analítica de features para el modelo y agregados para el dashboard.
# MAGIC DataFrame API.

# COMMAND ----------

dbutils.widgets.text("catalogo", "catalog_dev", "Catálogo")
dbutils.widgets.text("esquema_source", "silver", "Schema origen")
dbutils.widgets.text("esquema_sink", "golden", "Schema destino")
dbutils.widgets.text("storageName", "stfrauddetection01", "Storage Account")

catalogo       = dbutils.widgets.get("catalogo")
esquema_source = dbutils.widgets.get("esquema_source")
esquema_sink   = dbutils.widgets.get("esquema_sink")
storageName    = dbutils.widgets.get("storageName")

base = f"abfss://golden@{storageName}.dfs.core.windows.net"

# COMMAND ----------

from pyspark.sql import functions as F

silver = spark.table(f"{catalogo}.{esquema_source}.transactions")

# COMMAND ----------

# MAGIC %md ## Tabla de features para el modelo

# COMMAND ----------

features = silver.select(
    "amt", "amt_log", "category", "gender", "edad", "hora",
    "dia_semana", "dist_geo", "city_pop", "is_fraud"
).na.drop(subset=["amt", "category", "gender", "edad", "dist_geo", "is_fraud"])

tabla_feat = f"{catalogo}.{esquema_sink}.transactions_features"
(features.write.format("delta").mode("overwrite")
 .option("path", f"{base}/transactions_features")
 .option("overwriteSchema", "true")
 .saveAsTable(tabla_feat))
print(f"OK: {tabla_feat} ({features.count()} filas)")

# COMMAND ----------

# MAGIC %md ## Agregados para el dashboard

# COMMAND ----------

fraud_by_cat = (silver.groupBy("category")
                .agg(F.count("*").alias("total"),
                     F.sum("is_fraud").alias("fraudes"),
                     F.round(F.avg("is_fraud") * 100, 3).alias("tasa_fraude_pct"))
                .orderBy(F.desc("tasa_fraude_pct")))
(fraud_by_cat.write.format("delta").mode("overwrite")
 .option("path", f"{base}/fraud_by_category").option("overwriteSchema", "true")
 .saveAsTable(f"{catalogo}.{esquema_sink}.fraud_by_category"))

fraud_by_hour = (silver.groupBy("hora")
                 .agg(F.count("*").alias("total"),
                      F.sum("is_fraud").alias("fraudes"),
                      F.round(F.avg("is_fraud") * 100, 3).alias("tasa_fraude_pct"))
                 .orderBy("hora"))
(fraud_by_hour.write.format("delta").mode("overwrite")
 .option("path", f"{base}/fraud_by_hour").option("overwriteSchema", "true")
 .saveAsTable(f"{catalogo}.{esquema_sink}.fraud_by_hour"))

print("Agregados golden creados.")
display(fraud_by_cat)
