# Databricks notebook source
# MAGIC %md
# MAGIC # Reversión: DROP de tablas/schemas y limpieza de rutas físicas
# MAGIC Deja el entorno limpio. **No** borra el contenedor raw (los insumos originales se conservan).

# COMMAND ----------

dbutils.widgets.text("catalogo", "catalog_dev", "Catálogo")
dbutils.widgets.text("storageName", "stfrauddetection01", "Storage Account")

catalogo    = dbutils.widgets.get("catalogo")
storageName = dbutils.widgets.get("storageName")

# COMMAND ----------

# Revocar grants (best-effort).
for stmt in [
    f"REVOKE ALL PRIVILEGES ON CATALOG {catalogo} FROM `ingenieros_datos`",
    f"REVOKE SELECT ON SCHEMA {catalogo}.golden FROM `analistas_fraude`",
]:
    try:
        spark.sql(stmt); print(f"OK: {stmt}")
    except Exception as e:
        print(f"WARN: {stmt} -> {e}")

# COMMAND ----------

# DROP de schemas en cascada (tablas lógicas).
for esquema in ["golden", "silver", "bronze", "ml"]:
    spark.sql(f"DROP SCHEMA IF EXISTS {catalogo}.{esquema} CASCADE")
    print(f"DROP SCHEMA {catalogo}.{esquema}")

# COMMAND ----------

# Limpieza de rutas físicas (external locations bronze/silver/golden). raw NO se toca.
for capa in ["bronze", "silver", "golden"]:
    path = f"abfss://{capa}@{storageName}.dfs.core.windows.net/"
    try:
        dbutils.fs.rm(path, True); print(f"rm {path}")
    except Exception as e:
        print(f"WARN rm {path} -> {e}")

print("Reversión completa.")
