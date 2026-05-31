# Databricks notebook source
# MAGIC %md
# MAGIC # 2. Transform (Bronze → Silver)
# MAGIC Unifica train/test, castea tipos, parsea fechas y deriva features base (edad, hora, día de semana,
# MAGIC distancia geográfica cliente-comercio). Todo con **DataFrame API** (sin spark.sql para datos).

# COMMAND ----------

dbutils.widgets.text("catalogo", "catalog_dev", "Catálogo")
dbutils.widgets.text("esquema_source", "bronze", "Schema origen")
dbutils.widgets.text("esquema_sink", "silver", "Schema destino")
dbutils.widgets.text("storageName", "stfrauddetection01", "Storage Account")

catalogo       = dbutils.widgets.get("catalogo")
esquema_source = dbutils.widgets.get("esquema_source")
esquema_sink   = dbutils.widgets.get("esquema_sink")
storageName    = dbutils.widgets.get("storageName")

silver_path = f"abfss://silver@{storageName}.dfs.core.windows.net/transactions"
tabla_sink  = f"{catalogo}.{esquema_sink}.transactions"

# COMMAND ----------

from pyspark.sql import functions as F

train = spark.table(f"{catalogo}.{esquema_source}.transactions_train")
test  = spark.table(f"{catalogo}.{esquema_source}.transactions_test")

# Unificar ambos insumos (DataFrame API).
df = train.unionByName(test, allowMissingColumns=True)
print(f"Filas unificadas: {df.count()}")

# COMMAND ----------

# Casting de tipos y parseo de fechas.
df = (df
      .withColumn("trans_ts", F.to_timestamp("trans_date_trans_time"))
      .withColumn("dob_date", F.to_date("dob"))
      .withColumn("amt", F.col("amt").cast("double"))
      .withColumn("lat", F.col("lat").cast("double"))
      .withColumn("long", F.col("long").cast("double"))
      .withColumn("merch_lat", F.col("merch_lat").cast("double"))
      .withColumn("merch_long", F.col("merch_long").cast("double"))
      .withColumn("city_pop", F.col("city_pop").cast("long"))
      .withColumn("is_fraud", F.col("is_fraud").cast("int")))

# COMMAND ----------

# Features derivadas.
df = (df
      .withColumn("edad", (F.datediff(F.col("trans_ts"), F.col("dob_date")) / 365.25).cast("int"))
      .withColumn("hora", F.hour("trans_ts"))
      .withColumn("dia_semana", F.dayofweek("trans_ts"))
      .withColumn("amt_log", F.log1p(F.col("amt"))))

# Distancia geográfica (haversine, km) entre cliente y comercio.
R = F.lit(6371.0)
dlat = F.radians(F.col("merch_lat") - F.col("lat"))
dlon = F.radians(F.col("merch_long") - F.col("long"))
a = (F.sin(dlat / 2) ** 2
     + F.cos(F.radians(F.col("lat"))) * F.cos(F.radians(F.col("merch_lat"))) * F.sin(dlon / 2) ** 2)
df = df.withColumn("dist_geo", R * 2 * F.asin(F.sqrt(a)))

# COMMAND ----------

# Limpieza: descartar filas sin objetivo o sin monto.
df_silver = (df
             .filter(F.col("is_fraud").isNotNull() & F.col("amt").isNotNull())
             .select("trans_num", "trans_ts", "cc_num", "merchant", "category", "amt", "amt_log",
                     "gender", "city", "state", "city_pop", "job", "edad", "hora", "dia_semana",
                     "lat", "long", "merch_lat", "merch_long", "dist_geo", "is_fraud"))

print(f"Filas silver: {df_silver.count()}")

# COMMAND ----------

(df_silver.write
 .format("delta")
 .mode("overwrite")
 .option("path", silver_path)
 .option("overwriteSchema", "true")
 .saveAsTable(tabla_sink))

print(f"Tabla silver creada: {tabla_sink}")
display(spark.table(tabla_sink).limit(5))
