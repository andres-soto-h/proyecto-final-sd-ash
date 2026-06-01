# Databricks notebook source
# MAGIC %md
# MAGIC # 1. Ingest TRAIN (Extract → Bronze)
# MAGIC Lee `fraudTrain.csv` desde el contenedor **raw** (Managed Identity) y lo escribe como tabla Delta externa en bronze.
# MAGIC Transformaciones con **DataFrame API** (sin spark.sql para datos).

# COMMAND ----------

dbutils.widgets.text("catalogo", "catalog_dev", "Catálogo")
dbutils.widgets.text("container", "raw", "Contenedor raw")
dbutils.widgets.text("esquema", "bronze", "Schema destino")
dbutils.widgets.text("storageName", "stfrauddetection01", "Storage Account")

catalogo    = dbutils.widgets.get("catalogo")
container   = dbutils.widgets.get("container")
esquema     = dbutils.widgets.get("esquema")
storageName = dbutils.widgets.get("storageName")

raw_path    = f"abfss://{container}@{storageName}.dfs.core.windows.net/fraudTrain.csv"
# Ruta namespaced por catálogo para que dev y prod no solapen ubicaciones de tablas externas.
bronze_path = f"abfss://bronze@{storageName}.dfs.core.windows.net/{catalogo}/transactions_train"
tabla       = f"{catalogo}.{esquema}.transactions_train"

# COMMAND ----------

from pyspark.sql.functions import current_timestamp, lit

df = (spark.read
      .option("header", True)
      .option("inferSchema", True)
      .csv(raw_path))

print(f"Filas leídas de raw: {df.count()}")
df.printSchema()

# COMMAND ----------

# Enriquecer con metadata de ingesta (DataFrame API).
df_bronze = (df
             .withColumn("ingestion_date", current_timestamp())
             .withColumn("source_file", lit("fraudTrain.csv")))

# COMMAND ----------

(df_bronze.write
 .format("delta")
 .mode("overwrite")
 .option("path", bronze_path)
 .option("overwriteSchema", "true")
 .saveAsTable(tabla))

print(f"Tabla bronze creada: {tabla}")
display(spark.table(tabla).limit(5))
