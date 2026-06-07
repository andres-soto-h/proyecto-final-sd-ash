# Spec 02 — Seguridad, Roles y Grants

## Objetivo

Definir el modelo de acceso: RBAC en Azure para que la capa raw se lea **solo con Managed Identity**, y los
**grants** de Unity Catalog a usuarios/grupos sobre el catálogo, schemas y tablas creados.

## Requisitos

1. La Managed Identity (Access Connector) debe tener **Storage Blob Data Contributor** sobre el Storage Account
   (creado en spec 01 vía `azurerm_role_assignment`).
2. Ningún acceso a raw debe usar account keys, SAS ni `dbutils.fs.mount` con secretos → solo Storage Credential.
3. Grupos/usuarios de Databricks con permisos diferenciados:
   - Grupo `analistas_fraude`: `USE CATALOG`, `USE SCHEMA`, `SELECT` sobre `golden`.
   - Grupo `ingenieros_datos`: `ALL PRIVILEGES` sobre el catálogo del entorno.
4. Los grupos se **crean desde el notebook** `proceso/5_grants.py` con el SDK (`WorkspaceClient`), de forma
   idempotente — sin tocar Terraform ni `account_id`, reutilizando la auth del job.
5. Grants idempotentes y versionados (`seguridad/grants.sql`), ejecutables como tarea final del pipeline.

## Diseño

### RBAC Azure (Terraform — spec 01)
- `azurerm_role_assignment` rol `Storage Blob Data Contributor`, scope = storage account, principal = MI del Access Connector.

### Grants Unity Catalog (`seguridad/grants.sql`)
```sql
-- parametrizado por catálogo (catalog_dev / catalog_prod)
GRANT USE CATALOG ON CATALOG ${catalogo} TO `analistas_fraude`;
GRANT USE SCHEMA  ON SCHEMA  ${catalogo}.golden TO `analistas_fraude`;
GRANT SELECT      ON SCHEMA  ${catalogo}.golden TO `analistas_fraude`;
GRANT ALL PRIVILEGES ON CATALOG ${catalogo} TO `ingenieros_datos`;
```
- Se ejecuta desde el notebook `5_grants` (última tarea del Job), recibiendo `catalogo` por widget.

### Reversión de permisos
- `reversion/` incluye `REVOKE` y `DROP` (ver spec 03).

## Tareas

1. Confirmar el `role_assignment` en `infra/02-databricks-ws.tf`.
2. Escribir `seguridad/grants.sql` parametrizado.
3. Notebook `proceso/5_grants.py`: crea los grupos (SDK, idempotente) y ejecuta los grants leyendo el widget `catalogo`.
4. Documentar grupos/usuarios y capturar evidencia (`evidencias/`).

## Criterios de aceptación

- La MI lee raw sin keys/SAS (verificado en spec 01).
- `seguridad/grants.sql` corre sin error y los grupos ven solo lo permitido.
- Evidencia de usuarios/grupos en el workspace.
