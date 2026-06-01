# Databricks notebook source
# MAGIC %md
# MAGIC # 2. Transform (Bronze → Silver)
# MAGIC Unifica train/test, castea tipos, parsea fechas y deriva features. Incluye **features de
# MAGIC comportamiento por tarjeta** (velocidad y desviación de monto) con window functions — sin fuga de
# MAGIC datos (solo usan transacciones previas de la misma tarjeta). Todo con **DataFrame API**.

# COMMAND ----------

dbutils.widgets.text("catalogo", "catalog_dev", "Catálogo")
dbutils.widgets.text("esquema_source", "bronze", "Schema origen")
dbutils.widgets.text("esquema_sink", "silver", "Schema destino")
dbutils.widgets.text("storageName", "stfrauddetection01", "Storage Account")

catalogo       = dbutils.widgets.get("catalogo")
esquema_source = dbutils.widgets.get("esquema_source")
esquema_sink   = dbutils.widgets.get("esquema_sink")
storageName    = dbutils.widgets.get("storageName")

silver_path = f"abfss://silver@{storageName}.dfs.core.windows.net/{catalogo}/transactions"
tabla_sink  = f"{catalogo}.{esquema_sink}.transactions"

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.window import Window

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
      .withColumn("unix_time", F.col("unix_time").cast("long"))
      .withColumn("is_fraud", F.col("is_fraud").cast("int")))

# COMMAND ----------

# Features derivadas simples.
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

# Flags de contexto temporal.
df = (df
      .withColumn("es_noche", ((F.col("hora") >= 22) | (F.col("hora") <= 5)).cast("int"))
      .withColumn("es_fin_semana", F.col("dia_semana").isin(1, 7).cast("int")))

# COMMAND ----------

# MAGIC %md ## Features de comportamiento por tarjeta (window functions, sin fuga)

# COMMAND ----------

# Ventanas por tarjeta ordenadas en el tiempo. Solo usan transacciones PREVIAS (no la actual ni futuras).
w_card      = Window.partitionBy("cc_num").orderBy("unix_time")
w_card_24h  = Window.partitionBy("cc_num").orderBy("unix_time").rangeBetween(-86400, -1)  # 24h previas
w_card_prev = Window.partitionBy("cc_num").orderBy("unix_time").rowsBetween(Window.unboundedPreceding, -1)

df = (df
      # segundos desde la transacción anterior de la misma tarjeta (-1 si es la primera)
      .withColumn("tiempo_desde_ultima_tx_seg",
                  (F.col("unix_time") - F.lag("unix_time").over(w_card)))
      # cantidad de transacciones de la tarjeta en las 24h previas
      .withColumn("n_tx_ultimas_24h", F.count(F.lit(1)).over(w_card_24h))
      # promedio histórico de monto de la tarjeta (transacciones previas)
      .withColumn("amt_avg_prev", F.avg("amt").over(w_card_prev))
      # razón del monto actual vs el promedio histórico de la tarjeta (1.0 si no hay historia)
      .withColumn("amt_vs_avg_tarjeta",
                  F.when(F.col("amt_avg_prev").isNotNull() & (F.col("amt_avg_prev") > 0),
                         F.col("amt") / F.col("amt_avg_prev")).otherwise(F.lit(1.0))))

# Imputación de nulos en features de comportamiento (primera transacción de cada tarjeta).
df = df.fillna({"tiempo_desde_ultima_tx_seg": -1, "n_tx_ultimas_24h": 0})

# COMMAND ----------

# Limpieza: descartar filas sin objetivo o sin monto, y seleccionar columnas finales.
df_silver = (df
             .filter(F.col("is_fraud").isNotNull() & F.col("amt").isNotNull())
             .select("trans_num", "trans_ts", "cc_num", "merchant", "category", "amt", "amt_log",
                     "gender", "city", "state", "city_pop", "job", "edad", "hora", "dia_semana",
                     "es_noche", "es_fin_semana", "lat", "long", "merch_lat", "merch_long", "dist_geo",
                     "tiempo_desde_ultima_tx_seg", "n_tx_ultimas_24h", "amt_vs_avg_tarjeta", "is_fraud"))

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
