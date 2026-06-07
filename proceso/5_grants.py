# Databricks notebook source
# MAGIC %md
# MAGIC # 5. Grants (seguridad)
# MAGIC Crea los **grupos** del proyecto (si no existen) y aplica los **permisos** de Unity Catalog.
# MAGIC Espejo de `seguridad/grants.sql`. Última tarea del pipeline (después de Load/Train).
# MAGIC
# MAGIC > Los grupos se crean con el SDK de Databricks (`WorkspaceClient`), que autentica solo con el
# MAGIC > contexto del job. Idempotente: si el grupo ya existe, no falla.

# COMMAND ----------

dbutils.widgets.text("catalogo", "catalog_dev", "Catálogo")
catalogo = dbutils.widgets.get("catalogo")
print(f"catalogo={catalogo}")

# COMMAND ----------

# MAGIC %md ## Crear grupos del proyecto (idempotente)
# MAGIC - `analistas_fraude`: consumo de la capa golden.
# MAGIC - `ingenieros_datos`: control total del catálogo.

# COMMAND ----------

from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
GRUPOS = ["analistas_fraude", "ingenieros_datos"]

for nombre in GRUPOS:
    try:
        existentes = list(w.groups.list(filter=f'displayName eq "{nombre}"'))
        if existentes:
            print(f"OK (ya existe): {nombre} -> id={existentes[0].id}")
        else:
            g = w.groups.create(display_name=nombre)
            print(f"CREADO: {nombre} -> id={g.id}")
    except Exception as e:
        # No abortar el pipeline; dejar trazado para revisar permisos/SCIM.
        print(f"WARN creando grupo {nombre}: {e}")

# COMMAND ----------

# MAGIC %md ## Aplicar grants de Unity Catalog

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
