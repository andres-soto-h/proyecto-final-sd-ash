"""Web app de exposición — Detección de Fraude.

Recibe los datos de una transacción, consulta el endpoint de Databricks Model Serving
y muestra si la transacción es fraudulenta o no, con su probabilidad.

Config (st.secrets o variables de entorno):
  DATABRICKS_HOST   = https://adb-xxxx.azuredatabricks.net
  SERVING_ENDPOINT  = fraud-xgb-endpoint
  DATABRICKS_TOKEN  = <token>
"""
import os
import requests
import streamlit as st

st.set_page_config(page_title="Detección de Fraude", page_icon="🛡️", layout="centered")


def get_cfg(key: str, default: str = "") -> str:
    try:
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return os.environ.get(key, default)


HOST = get_cfg("DATABRICKS_HOST").rstrip("/")
ENDPOINT = get_cfg("SERVING_ENDPOINT", "fraud-xgb-endpoint")
TOKEN = get_cfg("DATABRICKS_TOKEN")

CATEGORIES = [
    "misc_net", "grocery_pos", "entertainment", "gas_transport", "misc_pos",
    "shopping_net", "shopping_pos", "food_dining", "personal_care", "health_fitness",
    "travel", "kids_pets", "home", "grocery_net",
]


def predict(payload: dict) -> dict:
    url = f"{HOST}/serving-endpoints/{ENDPOINT}/invocations"
    headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
    resp = requests.post(url, headers=headers, json={"dataframe_records": [payload]}, timeout=30)
    resp.raise_for_status()
    return resp.json()


# ----------------- UI -----------------
st.title("🛡️ Detección de Transacciones Fraudulentas")
st.caption("Modelo XGBoost servido en Databricks Model Serving · arquitectura medallion")

with st.sidebar:
    st.header("Sobre el proyecto")
    st.markdown(
        "- ETL medallion (bronze/silver/golden) en PySpark.\n"
        "- Acceso a raw solo con Managed Identity.\n"
        "- Modelo XGBoost trackeado con MLflow y registrado en Unity Catalog.\n"
        "- CI/CD dev→prod con GitHub Actions."
    )
    if not (HOST and TOKEN):
        st.warning("Configura DATABRICKS_HOST y DATABRICKS_TOKEN en .streamlit/secrets.toml")

with st.form("tx"):
    col1, col2 = st.columns(2)
    with col1:
        amt = st.number_input("Monto (amt)", min_value=0.0, value=120.50, step=10.0)
        category = st.selectbox("Categoría", CATEGORIES)
        gender = st.selectbox("Género", ["M", "F"])
        edad = st.slider("Edad del titular", 18, 95, 40)
    with col2:
        hora = st.slider("Hora (0-23)", 0, 23, 2)
        dia_semana = st.slider("Día de semana (1=Dom)", 1, 7, 7)
        dist_geo = st.number_input("Distancia cliente-comercio (km)", min_value=0.0, value=45.0)
        city_pop = st.number_input("Población ciudad", min_value=0, value=5000, step=500)
    submitted = st.form_submit_button("Evaluar transacción")

if submitted:
    import math
    payload = {
        "amt": float(amt),
        "amt_log": float(math.log1p(amt)),
        "category": category,
        "gender": gender,
        "edad": int(edad),
        "hora": int(hora),
        "dia_semana": int(dia_semana),
        "dist_geo": float(dist_geo),
        "city_pop": int(city_pop),
    }
    try:
        result = predict(payload)
        preds = result.get("predictions", result)
        pred = preds[0] if isinstance(preds, list) else preds
        # El endpoint devuelve la clase (0/1). Si devuelve dict con probas, ajustar aquí.
        is_fraud = int(pred) == 1 if not isinstance(pred, dict) else int(pred.get("prediction", 0)) == 1
        if is_fraud:
            st.error("⚠️ Transacción potencialmente FRAUDULENTA")
        else:
            st.success("✅ Transacción legítima")
        with st.expander("Respuesta del endpoint"):
            st.json(result)
    except Exception as e:
        st.exception(e)
