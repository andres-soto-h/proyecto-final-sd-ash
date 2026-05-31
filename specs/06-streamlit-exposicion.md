# Spec 06 — Web App de Exposición (Streamlit)

## Objetivo

Construir una web app en **Streamlit** que reciba los datos de una transacción, llame al endpoint de
**Databricks Model Serving** y muestre si la transacción es **fraudulenta o no** con su probabilidad.

## Requisitos

1. Formulario con los campos de entrada (features de golden): `amt, category, gender, edad, hora,
   dia_semana, dist_geo, city_pop`.
2. Llamada REST al endpoint de serving con autenticación por token Databricks.
3. Salida: etiqueta (Fraude / Legítima) + probabilidad + indicador visual.
4. Sin secretos en el repo: token vía `.streamlit/secrets.toml` (ignorado) o variables de entorno.

## Diseño

### `streamlit_app/app.py`
- Lee `DATABRICKS_HOST`, `SERVING_ENDPOINT`, `DATABRICKS_TOKEN` desde `st.secrets`/env.
- Construye el payload `{"dataframe_records": [ {features...} ]}` (formato Model Serving).
- `requests.post(f"{host}/serving-endpoints/{endpoint}/invocations", headers=Bearer, json=payload)`.
- Muestra resultado con `st.metric` / `st.error`/`st.success` según predicción.
- Sidebar con descripción del proyecto y arquitectura.

### Archivos
- `app.py`, `requirements.txt` (`streamlit`, `requests`, `pandas`),
  `.streamlit/secrets.toml.example`.

### Hosting
- Local (`streamlit run`) para la demo/evidencia; opción de Streamlit Community Cloud (repo público).

## Tareas

1. Escribir `app.py` con formulario + llamada al endpoint + render del resultado.
2. `requirements.txt` y `secrets.toml.example`.
3. Capturar evidencia de la app prediciendo (fraude y no fraude).

## Criterios de aceptación

- `streamlit run streamlit_app/app.py` levanta la app.
- Ingresar una transacción devuelve fraude/no-fraude + probabilidad desde el endpoint real.
- Sin secretos commiteados.
