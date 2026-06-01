"""Web app de exposición — Detección de Fraude.

Recibe los datos de una transacción, consulta el endpoint de Databricks Model Serving
(modelo XGBoost registrado en Unity Catalog) y muestra si la transacción es fraudulenta.

Config (st.secrets o variables de entorno):
  DATABRICKS_HOST   = https://adb-xxxx.azuredatabricks.net
  SERVING_ENDPOINT  = fraud-xgb-endpoint
  DATABRICKS_TOKEN  = <token / AAD bearer>
"""
import os
import math
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


def predict(record: dict):
    url = f"{HOST}/serving-endpoints/{ENDPOINT}/invocations"
    headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
    resp = requests.post(url, headers=headers, json={"dataframe_records": [record]}, timeout=60)
    resp.raise_for_status()
    return resp.json()


# ----------------- UI -----------------
st.title("🛡️ Detección de Transacciones Fraudulentas")
st.caption("Modelo XGBoost (Unity Catalog) servido en Databricks Model Serving · arquitectura medallion")

with st.sidebar:
    st.header("Sobre el proyecto")
    st.markdown(
        "- ETL medallion (bronze/silver/golden) en PySpark.\n"
        "- Acceso a `raw` solo con Managed Identity.\n"
        "- XGBoost con optimización de hiperparámetros (Hyperopt) + MLflow, registrado en Unity Catalog.\n"
        "- Features de comportamiento por tarjeta (velocidad, desviación de monto).\n"
        "- CI/CD dev→prod con GitHub Actions."
    )
    if not (HOST and TOKEN):
        st.warning("Configura DATABRICKS_HOST y DATABRICKS_TOKEN en .streamlit/secrets.toml")

with st.form("tx"):
    st.subheader("Datos de la transacción")
    col1, col2 = st.columns(2)
    with col1:
        amt = st.number_input("Monto (amt)", min_value=0.0, value=120.50, step=10.0)
        category = st.selectbox("Categoría", CATEGORIES)
        gender = st.selectbox("Género", ["M", "F"])
        edad = st.slider("Edad del titular", 18, 95, 40)
        hora = st.slider("Hora (0-23)", 0, 23, 2)
    with col2:
        dia_semana = st.slider("Día de semana (1=Dom … 7=Sáb)", 1, 7, 7)
        dist_geo = st.number_input("Distancia cliente-comercio (km)", min_value=0.0, value=45.0)
        city_pop = st.number_input("Población ciudad", min_value=0, value=5000, step=500)

    st.subheader("Comportamiento de la tarjeta")
    col3, col4, col5 = st.columns(3)
    with col3:
        n_tx_ultimas_24h = st.number_input("Tx en últimas 24h", min_value=0, value=2, step=1)
    with col4:
        tiempo_desde_ultima_tx_seg = st.number_input("Seg. desde última tx", min_value=-1, value=3600, step=60)
    with col5:
        amt_vs_avg_tarjeta = st.number_input("Monto vs promedio tarjeta (×)", min_value=0.0, value=1.0, step=0.5)

    submitted = st.form_submit_button("Evaluar transacción")

if submitted:
    record = {
        "category": category,
        "gender": gender,
        "amt": float(amt),
        "amt_log": float(math.log1p(amt)),
        "edad": int(edad),
        "hora": int(hora),
        "dia_semana": int(dia_semana),
        "es_noche": int(hora >= 22 or hora <= 5),
        "es_fin_semana": int(dia_semana in (1, 7)),
        "dist_geo": float(dist_geo),
        "city_pop": int(city_pop),
        "tiempo_desde_ultima_tx_seg": int(tiempo_desde_ultima_tx_seg),
        "n_tx_ultimas_24h": int(n_tx_ultimas_24h),
        "amt_vs_avg_tarjeta": float(amt_vs_avg_tarjeta),
    }
    try:
        result = predict(record)
        preds = result.get("predictions", result)
        pred = preds[0] if isinstance(preds, list) else preds
        is_fraud = int(pred) == 1
        if is_fraud:
            st.error("⚠️ Transacción potencialmente FRAUDULENTA")
        else:
            st.success("✅ Transacción legítima")
        with st.expander("Detalle"):
            st.write("**Flags derivados:** es_noche =", record["es_noche"], "· es_fin_semana =", record["es_fin_semana"])
            st.json(result)
    except Exception as e:
        st.exception(e)
