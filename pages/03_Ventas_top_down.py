# pages/03_Ventas_top_down.py
import datetime as dt
from zoneinfo import ZoneInfo
import streamlit as st

st.set_page_config(page_title="Paso 3A: Ventas Top-down", page_icon="📈")

TZ = ZoneInfo("America/Costa_Rica")

# ========================= 
# PASO 3A – Ventas (Top-down / declaración directa)
# =========================
def _mes_anterior_label():
    """Devuelve ('mes nombre año', 'YYYY-MM') del mes calendario anterior en TZ CR."""
    now = dt.datetime.now(TZ)
    year, month = now.year, now.month
    if month == 1:
        prev_year, prev_month = year - 1, 12
    else:
        prev_year, prev_month = year, month - 1
    meses_es = ["enero","febrero","marzo","abril","mayo","junio",
                "julio","agosto","septiembre","octubre","noviembre","diciembre"]
    etiqueta = f"{meses_es[prev_month-1]} {prev_year}"
    iso_ym = f"{prev_year:04d}-{prev_month:02d}"
    return etiqueta, iso_ym

def init_paso3A_state():
    st.session_state.setdefault("ventas_topdown", {})
    vtd = st.session_state.ventas_topdown
    vtd.setdefault("monto", 0)
    vtd.setdefault("tipicidad", "")  # "", "Típico", "Alto", "Bajo"
    vtd.setdefault("fuente", "")     # lista de opciones abajo
    vtd.setdefault("fuente_otro", "")
    vtd.setdefault("confianza_cliente", 5)  # 0–10
    vtd.setdefault("comentario", "")

# ---------- UI (multipágina; sin 'step') ----------
init_paso3A_state()
vtd = st.session_state.ventas_topdown
mes_etiqueta, mes_iso = _mes_anterior_label()

st.title("📈 Paso 3A: Ventas – Top-down (declaración directa)")
st.caption(f"Ingrese las ventas del último mes calendario: **{mes_etiqueta}**.")

with st.container():
    col1, col2 = st.columns([0.55, 0.45])
    with col1:
        vtd["monto"] = st.number_input(
            f"Ventas de {mes_etiqueta} (₡) *",
            min_value=0, step=1000, value=int(vtd["monto"]),
            help="Monto total vendido en el mes calendario anterior."
        )
        vtd["tipicidad"] = st.selectbox(
            "¿Ese mes fue…? *",
            options=["", "Típico", "Alto", "Bajo"],
            index=["", "Típico", "Alto", "Bajo"].index(vtd["tipicidad"]) if vtd["tipicidad"] in ["", "Típico", "Alto", "Bajo"] else 0,
            help="Cómo se compara ese mes con un mes normal del negocio."
        )
    with col2:
        fuente_opts = [
            "", "Facturación electrónica", "POS/Datáfono",
            "Extractos bancarios/SINPE", "Cuaderno/Excel", "Memoria", "Otro"
        ]
        vtd["fuente"] = st.selectbox(
            "Fuente del dato *",
            options=fuente_opts,
            index=fuente_opts.index(vtd["fuente"]) if vtd["fuente"] in fuente_opts else 0,
            help="De dónde sale el monto declarado."
        )
        if vtd["fuente"] == "Otro":
            vtd["fuente_otro"] = st.text_input(
                "Especifique la fuente",
                value=vtd.get("fuente_otro", "")
            )
        vtd["confianza_cliente"] = st.slider(
            "Confianza declarada por el cliente (0–10)",
            min_value=0, max_value=10, step=1, value=int(vtd["confianza_cliente"]),
            help="En una escala de 0 a 10, ¿qué tan seguro está del monto del último mes?"
        )

vtd["comentario"] = st.text_area(
    "Comentario (opcional)",
    value=vtd["comentario"],
    placeholder="Notas breves: p. ej., promociones, feriados, cierres, etc.",
    height=80
)

st.divider()

# -------- Validación obligatorios --------
fuente_valida = (vtd["fuente"] and vtd["fuente"] != "Otro") or (vtd["fuente"] == "Otro" and vtd["fuente_otro"].strip())
obligatorios_ok = all([
    vtd["monto"] > 0,
    vtd["tipicidad"] in ["Típico", "Alto", "Bajo"],
    fuente_valida
])

colNav1, colNav2 = st.columns([0.5, 0.5])
with colNav1:
    if st.button("⬅️ Volver al Paso 2", key="back_to_step_2", use_container_width=True):
        st.switch_page("pages/02_Cliente_y_negocio.py")

with colNav2:
    if st.button("Siguiente ➡️ (4)", key="next_step_3A", disabled=not obligatorios_ok, use_container_width=True):
        # Guardar bloque de reporte Top-down
        st.session_state.setdefault("reporte", {})
        fuente_final = vtd["fuente_otro"].strip() if vtd["fuente"] == "Otro" else vtd["fuente"]
        st.session_state["reporte"]["ventas_topdown"] = {
            "mes_referencia": mes_etiqueta,
            "mes_iso": mes_iso,  # YYYY-MM para cálculos
            "monto_colones": int(vtd["monto"]),
            "tipicidad": vtd["tipicidad"],
            "fuente": fuente_final,
            "confianza_cliente_0a10": int(vtd["confianza_cliente"]),
            "comentario": vtd["comentario"].strip(),
        }
        st.session_state["done_03A"] = True

        # Ir al Paso 4 – Ventas Bottom-up (según tu nombre de archivo)
        try:
            st.switch_page("pages/04_Ventas_botton_up.py")
        except Exception:
            st.success("Ventas Top-down guardadas. Abre el **Paso 4 – Ventas Bottom-up** desde el menú lateral.")
            st.stop()


