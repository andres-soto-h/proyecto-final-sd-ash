-- Grants de Unity Catalog para el proyecto de detección de fraude.
-- Parametrizado por ${catalogo} (catalog_dev / catalog_prod).
-- Los grupos los crea (idempotente) el notebook `proceso/5_grants.py` vía SDK antes de estos grants:
--   - analistas_fraude : consumo de la capa golden.
--   - ingenieros_datos : control total del catálogo.

-- Analistas: solo lectura sobre golden.
GRANT USE CATALOG ON CATALOG ${catalogo} TO `analistas_fraude`;
GRANT USE SCHEMA  ON SCHEMA  ${catalogo}.golden TO `analistas_fraude`;
GRANT SELECT      ON SCHEMA  ${catalogo}.golden TO `analistas_fraude`;

-- Ingenieros de datos: control total del catálogo.
GRANT ALL PRIVILEGES ON CATALOG ${catalogo} TO `ingenieros_datos`;
