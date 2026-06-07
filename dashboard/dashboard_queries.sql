-- ============================================================================
-- Tablero de Detección de Fraude — consultas sobre la capa GOLDEN
-- ----------------------------------------------------------------------------
-- Pega cada consulta en Databricks SQL (Query nueva) y crea su visualización.
-- Parametrizadas por ${catalogo} (catalog_dev / catalog_prod): usa un parámetro
-- de tipo texto llamado "catalogo", o reemplaza ${catalogo} por el catálogo real.
-- Fuente: tablas creadas en proceso/3_load.py
--   - {catalogo}.golden.fraud_by_category
--   - {catalogo}.golden.fraud_by_hour
--   - {catalogo}.golden.transactions_features
-- ============================================================================


-- 1) KPIs globales  [Visualización: Counter, uno por métrica]
-- Total de transacciones, fraudes detectados y tasa de fraude global.
SELECT
  COUNT(*)                                    AS total_transacciones,
  SUM(is_fraud)                               AS total_fraudes,
  ROUND(AVG(is_fraud) * 100, 3)               AS tasa_fraude_pct
FROM ${catalogo}.golden.transactions_features;


-- 2) Monto promedio: legítimo vs fraude  [Visualización: Bar chart]
-- Los fraudes suelen tener un ticket promedio distinto; lo evidenciamos.
SELECT
  CASE WHEN is_fraud = 1 THEN 'Fraude' ELSE 'Legítima' END AS tipo,
  COUNT(*)                                                  AS transacciones,
  ROUND(AVG(amt), 2)                                        AS monto_promedio,
  ROUND(MAX(amt), 2)                                        AS monto_max
FROM ${catalogo}.golden.transactions_features
GROUP BY is_fraud
ORDER BY is_fraud;


-- 3) Tasa de fraude por categoría  [Visualización: Bar chart horizontal]
-- X = category, Y = tasa_fraude_pct. Ordenado de mayor a menor riesgo.
SELECT category, total, fraudes, tasa_fraude_pct
FROM ${catalogo}.golden.fraud_by_category
ORDER BY tasa_fraude_pct DESC;


-- 4) Tasa de fraude por hora del día  [Visualización: Line chart]
-- X = hora (0-23), Y = tasa_fraude_pct. Resalta el patrón nocturno (feature es_noche).
SELECT hora, total, fraudes, tasa_fraude_pct
FROM ${catalogo}.golden.fraud_by_hour
ORDER BY hora;


-- 5) Fraude día vs noche  [Visualización: Pie / Bar]
-- Confirma que la franja nocturna concentra mayor tasa de fraude.
SELECT
  CASE WHEN es_noche = 1 THEN 'Noche (22h-5h)' ELSE 'Día (6h-21h)' END AS franja,
  COUNT(*)                          AS transacciones,
  SUM(is_fraud)                     AS fraudes,
  ROUND(AVG(is_fraud) * 100, 3)     AS tasa_fraude_pct
FROM ${catalogo}.golden.transactions_features
GROUP BY es_noche
ORDER BY es_noche DESC;


-- 6) Tasa de fraude: fin de semana vs entre semana  [Visualización: Bar chart]
SELECT
  CASE WHEN es_fin_semana = 1 THEN 'Fin de semana' ELSE 'Entre semana' END AS periodo,
  COUNT(*)                          AS transacciones,
  SUM(is_fraud)                     AS fraudes,
  ROUND(AVG(is_fraud) * 100, 3)     AS tasa_fraude_pct
FROM ${catalogo}.golden.transactions_features
GROUP BY es_fin_semana
ORDER BY es_fin_semana DESC;


-- 7) Fraude por rango de monto  [Visualización: Bar chart]
-- Segmenta el monto en tramos y mide la tasa de fraude por tramo.
SELECT
  CASE
    WHEN amt < 50    THEN '0-50'
    WHEN amt < 100   THEN '50-100'
    WHEN amt < 250   THEN '100-250'
    WHEN amt < 500   THEN '250-500'
    WHEN amt < 1000  THEN '500-1000'
    ELSE '1000+'
  END                               AS rango_monto,
  COUNT(*)                          AS transacciones,
  SUM(is_fraud)                     AS fraudes,
  ROUND(AVG(is_fraud) * 100, 3)     AS tasa_fraude_pct
FROM ${catalogo}.golden.transactions_features
GROUP BY 1
ORDER BY MIN(amt);
