# Databricks notebook source
# MAGIC %md
# MAGIC # 0. Preparación de Ambiente
# MAGIC Crea los **schemas** del medallion (bronze/silver/golden) y el schema `ml`.
# MAGIC
# MAGIC > El catálogo, el storage credential y los external locations los crea **Terraform** (spec 01).
# MAGIC > Aquí solo se crean schemas. Las tablas se crean al escribir (external Delta) en los notebooks de ingest/transform/load.

# COMMAND ----------

dbutils.widgets.text("catalogo", "catalog_dev", "Catálogo Unity Catalog")
dbutils.widgets.text("storageName", "stfrauddetection01", "Storage Account")

catalogo    = dbutils.widgets.get("catalogo")
storageName = dbutils.widgets.get("storageName")
print(f"catalogo={catalogo} | storageName={storageName}")

# COMMAND ----------

# MAGIC %md ## Crear schemas del medallion

# COMMAND ----------

for esquema in ["bronze", "silver", "golden", "ml"]:
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalogo}.{esquema} "
              f"COMMENT 'Capa {esquema} - arquitectura medallion fraude'")
    print(f"Schema listo: {catalogo}.{esquema}")

# COMMAND ----------

display(spark.sql(f"SHOW SCHEMAS IN {catalogo}"))

# COMMAND ----------

# MAGIC %md Ambiente preparado. Continuar con los notebooks de ingest.
