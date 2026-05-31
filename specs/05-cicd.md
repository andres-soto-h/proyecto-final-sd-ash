# Spec 05 — CI/CD dev → prod con GitHub Actions

## Objetivo

Automatizar el despliegue de dev a prod: al hacer push a `main`, exportar los notebooks del workspace **dev**,
importarlos al workspace **prod**, crear el **Job multi-task** (medallion + ML) y ejecutarlo, monitoreando el resultado.

## Requisitos

1. Disparo en `push` a `main`.
2. Integrar como tareas del pipeline (rúbrica `ejemplo1.png`/`ejemplo2.png`):
   `prepAmb → ingest(extract) → transform → load → train → grants`.
3. Patrón export/import vía Databricks REST API (igual a los repos de referencia) + Jobs API 2.1.
4. Monitoreo de la ejecución con salida clara (éxito/falla).
5. Secrets en GitHub (no en repo).

## Diseño

### `.github/workflows/deploy-databricks.yml`
Pasos:
1. Checkout.
2. Export notebooks desde DEV (`/api/2.0/workspace/export?format=SOURCE`).
3. Import a PROD (`/api/2.0/workspace/mkdirs` + `/api/2.0/workspace/import`).
4. Obtener `cluster_id` existente en prod (o usar job cluster).
5. Borrar Job previo si existe (`jobs/list` + `jobs/delete`).
6. Crear Job multi-task (`jobs/create`) con dependencias:
   `prepamb → [ingest_train, ingest_test] → transform → load → train → grants`,
   con `base_parameters` (catalogo=catalog_prod, storageName, esquemas).
7. Ejecutar (`jobs/run-now`) y monitorear (`jobs/runs/get`).

### Secrets requeridos (GitHub → Settings → Secrets)
- `DATABRICKS_ORIGIN_HOST`, `DATABRICKS_ORIGIN_TOKEN` (workspace dev).
- `DATABRICKS_DEST_HOST`, `DATABRICKS_DEST_TOKEN` (workspace prod).

### `.github/workflows/terraform.yml` (opcional, gated por `workflow_dispatch`)
- `terraform fmt -check`, `validate`, `plan` (apply manual aprobado).

## Tareas

1. Escribir `deploy-databricks.yml` con las tareas y dependencias del medallion + train + grants.
2. Documentar los secrets en README.
3. Probar push a `main` y capturar evidencia (Actions verde + Job en prod).

## Criterios de aceptación

- Push a `main` dispara el workflow y corre verde.
- En prod quedan los notebooks importados y el Job ejecutado correctamente.
- Evidencias en `evidencias/` (Actions + Job run).
