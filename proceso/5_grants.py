# Databricks notebook source
# MAGIC %md
# MAGIC # 5. Grants (seguridad)
# MAGIC Aplica los permisos de Unity Catalog a los grupos del proyecto. Espejo de `seguridad/grants.sql`.
# MAGIC Última tarea del pipeline (después de Load/Train).

# COMMAND ----------

dbutils.widgets.text("catalogo", "catalog_dev", "Catálogo")
catalogo = dbutils.widgets.get("catalogo")

# COMMAND ----------

grants = [
    f"GRANT USE CATALOG ON CATALOG {catalogo} TO `analistas_fraude`",
    f"GRANT USE SCHEMA  ON SCHEMA  {catalogo}.golden TO `analistas_fraude`",
    f"GRANT SELECT      ON SCHEMA  {catalogo}.golden TO `analistas_fraude`",
    f"GRANT ALL PRIVILEGES ON CATALOG {catalogo} TO `ingenieros_datos`",
]

for stmt in grants:
    try:
        spark.sql(stmt)
        print(f"OK: {stmt}")
    except Exception as e:
        # No abortar el pipeline si el grupo aún no existe; dejar trazado.
        print(f"WARN: {stmt} -> {e}")

# COMMAND ----------

display(spark.sql(f"SHOW GRANTS ON CATALOG {catalogo}"))
