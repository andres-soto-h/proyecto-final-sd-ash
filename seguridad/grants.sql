-- Grants de Unity Catalog para el proyecto de detección de fraude.
-- Parametrizado por ${catalogo} (catalog_dev / catalog_prod).
-- Grupos esperados (crear en la consola de cuenta de Databricks):
--   - analistas_fraude : consumo de la capa golden.
--   - ingenieros_datos : control total del catálogo.

-- Analistas: solo lectura sobre golden.
GRANT USE CATALOG ON CATALOG ${catalogo} TO `analistas_fraude`;
GRANT USE SCHEMA  ON SCHEMA  ${catalogo}.golden TO `analistas_fraude`;
GRANT SELECT      ON SCHEMA  ${catalogo}.golden TO `analistas_fraude`;

-- Ingenieros de datos: control total del catálogo.
GRANT ALL PRIVILEGES ON CATALOG ${catalogo} TO `ingenieros_datos`;
