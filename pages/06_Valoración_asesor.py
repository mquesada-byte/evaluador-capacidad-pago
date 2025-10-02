# pages/06_Valoración_asesor.py
import streamlit as st
from utils.db import load_visita, save_valoracion_asesor
import datetime as dt
from zoneinfo import ZoneInfo

st.set_page_config(page_title="Paso 6: Valoración del asesor", page_icon="📝")

TZ = ZoneInfo("America/Costa_Rica")

def _mes_anterior_label():
    now = dt.datetime.now(TZ)
    year, month = now.year, now.month
    if month == 1:
        prev_year, prev_month = year - 1, 12
    else:
        prev_year, prev_month = year, month - 1
    return f"{prev_year:04d}-{prev_month:02d}"

def init_valoracion_asesor_state(cliente_id: str, mes_iso: str):
    st.session_state.setdefault("valoracion_asesor", {})
    v = st.session_state.valoracion_asesor

    datos = load_visita(cliente_id)
    if datos and "valoracion_asesor" in datos:
        db_row = datos["valoracion_asesor"]
        v["conocimiento_0a10"] = db_row.get("conocimiento_0a10") or 5
        v["credibilidad_0a10"] = db_row.get("credibilidad_0a10") or 5
        v["dudas_declaracion"] = db_row.get("dudas_declaracion") or "Sin dudas"
        v["clasificacion"] = db_row.get("clasificacion") or "Microempresario/a"
        v["evidencia"] = (db_row.get("evidencia") or "").split(",") if db_row.get("evidencia") else []
        v["comentario"] = db_row.get("comentario") or ""
    else:
        v.setdefault("conocimiento_0a10", 5)
        v.setdefault("credibilidad_0a10", 5)
        v.setdefault("dudas_declaracion", "Sin dudas")
        v.setdefault("clasificacion", "Microempresario/a")
        v.setdefault("evidencia", [])
        v.setdefault("comentario", "")


def _factor_asesor(v: dict) -> float:
    know = float(v.get("conocimiento_0a10") or 0)
    cred = float(v.get("credibilidad_0a10") or 0)
    avg = (know + cred) / 2.0
    base = 0.6 + 0.04 * avg
    dudas = v.get("dudas_declaracion", "Sin dudas")
    mult = {"Sin dudas": 1.0, "Dudas leves": 0.85, "Dudas serias": 0.60}.get(dudas, 1.0)
    return max(0.40, min(1.00, base * mult))

# --------- UI ----------
mes_iso = _mes_anterior_label()
cliente_id = st.session_state.get("cliente", {}).get("identificacion")

init_valoracion_asesor_state(cliente_id, mes_iso)
v = st.session_state.valoracion_asesor

st.title("📝 Paso 6: Valoración del asesor")

col1, col2 = st.columns(2)
with col1:
    v["conocimiento_0a10"] = st.slider("Conocimiento (0–10)", 0, 10, int(v["conocimiento_0a10"]))
with col2:
    v["credibilidad_0a10"] = st.slider("Credibilidad (0–10)", 0, 10, int(v["credibilidad_0a10"]))

col3, col4 = st.columns(2)
with col3:
    v["dudas_declaracion"] = st.selectbox("Percepción veracidad",
        ["Sin dudas", "Dudas leves", "Dudas serias"],
        index=["Sin dudas","Dudas leves","Dudas serias"].index(v["dudas_declaracion"]))
with col4:
    v["clasificacion"] = st.selectbox("Clasificación",
        ["Microempresario/a", "Actividad incipiente", "Dudoso / posible no negocio"],
        index=["Microempresario/a", "Actividad incipiente", "Dudoso / posible no negocio"].index(v["clasificacion"]))

v["evidencia"] = st.multiselect("Evidencia observada",
    ["Facturación/POS","Extractos bancarios","Cuaderno/Excel","Fotos del negocio","Ninguna"],
    default=v.get("evidencia", []))

v["comentario"] = st.text_area("Comentario", value=v.get("comentario") or "", height=90)

factor = _factor_asesor(v)
st.info(f"**Factor asesor:** {factor:.2f}")

colb1, colb2 = st.columns(2)
with colb1:
    if st.button("⬅️ Volver a 5", use_container_width=True):
        st.switch_page("pages/05_Ventas_insumos_margen.py")

with colb2:
    if st.button("Continuar ➡️ Conciliación", use_container_width=True):
        reporte = {
            "mes_iso": mes_iso,
            "conocimiento_0a10": int(v["conocimiento_0a10"]),
            "credibilidad_0a10": int(v["credibilidad_0a10"]),
            "dudas_declaracion": v["dudas_declaracion"],
            "clasificacion": v["clasificacion"],
            "evidencia": v["evidencia"],
            "comentario": v["comentario"].strip(),
            "factor_asesor_0a1": float(factor),
        }
        st.session_state.setdefault("reporte", {})
        st.session_state["reporte"]["valoracion_asesor"] = reporte
        st.session_state["done_06"] = True

        if cliente_id:
            save_valoracion_asesor(cliente_id, reporte)

        try:
            st.switch_page("pages/07_Conciliacion_de_ventas.py")
        except Exception:
            st.success("Valoración guardada. Abrí **Conciliación** desde el menú lateral.")
            st.stop()


