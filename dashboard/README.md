# Tablero — Detección de Fraude

Tablero analítico construido sobre la capa **golden** del medallion. Responde preguntas de negocio
sobre el riesgo de fraude: ¿dónde, cuándo y en qué montos se concentra?

## Cómo construirlo en Databricks SQL
1. Abre **SQL → Queries → Create query** en el workspace.
2. Pega cada consulta de [`dashboard_queries.sql`](./dashboard_queries.sql). Las consultas usan el
   parámetro de texto `catalogo` (`catalog_dev` o `catalog_prod`); créalo o reemplaza `${catalogo}`.
3. En cada query, pestaña **Visualization** → crea la visualización indicada en el comentario.
4. **SQL → Dashboards → Create dashboard** y agrega cada visualización como widget.
5. Exporta/captura el tablero final y coloca la imagen en este folder (ver más abajo).

## Paneles del tablero

| # | Panel | Fuente (golden) | Visualización | Qué muestra |
|---|-------|-----------------|---------------|-------------|
| 1 | KPIs globales | `transactions_features` | Counter | Total tx, fraudes y tasa global |
| 2 | Monto legítimo vs fraude | `transactions_features` | Bar | Ticket promedio/máx por tipo |
| 3 | Tasa de fraude por categoría | `fraud_by_category` | Bar horizontal | Categorías de mayor riesgo |
| 4 | Tasa de fraude por hora | `fraud_by_hour` | Line | Patrón horario (pico nocturno) |
| 5 | Fraude día vs noche | `transactions_features` | Pie / Bar | Concentración en franja nocturna (`es_noche`) |
| 6 | Fin de semana vs entre semana | `transactions_features` | Bar | Estacionalidad semanal (`es_fin_semana`) |
| 7 | Fraude por rango de monto | `transactions_features` | Bar | Tramos de monto con mayor tasa |

> Los paneles se alinean con las features de mayor peso del modelo (`es_noche`, `amt_vs_avg_tarjeta`),
> conectando el análisis exploratorio con lo que aprende el XGBoost.

## Evidencia
Coloca aquí la captura del tablero final (PNG), p. ej. `tablero-fraude.png`.
