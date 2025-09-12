# pages/05_Ventas_insumos_margen.py
import streamlit as st
import datetime as dt
from zoneinfo import ZoneInfo

from utils.db import load_visita, save_ventas_p5

st.set_page_config(page_title="Paso 5: Ventas (insumos/margen, comisión o costo % ventas)", page_icon="🧮")

TZ = ZoneInfo("America/Costa_Rica")

# =========================
# Utilidades
# =========================
def _mes_anterior_label():
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

def _fmt_crc(n):
    return f"₡ {int(round(n)):,}".replace(",", ".")

# =========================
# Estado inicial
# =========================
def init_paso5_state(cliente_id: str, mes_iso: str):
    st.session_state.setdefault("ventas_p5", {})
    st.session_state.setdefault("no_data_p5", False)
    vin = st.session_state.ventas_p5

    datos = load_visita(cliente_id)
    if datos and "ventas_p5" in datos:
        db_row = datos["ventas_p5"]
        if db_row.get("mes_iso") == mes_iso:
            st.session_state.no_data_p5 = (db_row.get("no_data") == 1)
            for k in [
                "modo", "tiene_registros", "compras_mes_colones", "tipo_margen",
                "margen_pct", "facturacion_bruta_mes_colones", "comision_pct",
                "ventas_reportadas_mes_colones", "costo_pct_sobre_ventas",
                "costo_estimado_colones", "ventas_estimadas_colones", "comentario"
            ]:
                vin[k] = db_row.get(k) or ("" if isinstance(db_row.get(k), str) else 0)
        else:
            _init_defaults(vin)
    else:
        _init_defaults(vin)

def _init_defaults(vin: dict):
    vin.setdefault("modo", "Bienes (insumos/margen)")
    vin.setdefault("tiene_registros_compras", "Sí")
    vin.setdefault("compras_mes", 0)
    vin.setdefault("tipo_margen", "Sobre ventas")
    vin.setdefault("margen_pct", 30)
    vin.setdefault("tiene_registros_fact", "Sí")
    vin.setdefault("facturacion_bruta_mes", 0)
    vin.setdefault("comision_pct", 10)
    vin.setdefault("ventas_reportadas_mes", 0)
    vin.setdefault("costo_pct_sobre_ventas", 10)
    vin.setdefault("comentario", "")

# =========================
# Cálculos (igual que antes)
# =========================
def _calc_ventas_bienes_desde_compras(compras, tipo_margen, margen_pct): ...
def _calc_ventas_servicio_comision(fact_bruta, comision_pct): ...
def _calc_servicio_costo_pct_ventas(ventas, costo_pct): ...

# =========================
# UI
# =========================
mes_etiqueta, mes_iso = _mes_anterior_label()
cliente_id = st.session_state.cliente.get("identificacion")

init_paso5_state(cliente_id, mes_iso)
vin = st.session_state.ventas_p5

st.title("🧮 Paso 5: Ventas")
st.caption(f"Mes de referencia: **{mes_etiqueta}**.")

st.session_state.no_data_p5 = st.checkbox(
    "No tengo datos para este mes",
    value=st.session_state.no_data_p5
)
is_disabled = st.session_state.no_data_p5

# 👉 ... [UI igual que tu código original, usando `is_disabled`] ...

# =========================
# Navegación
# =========================
if st.session_state.no_data_p5:
    oblig_ok = True

colNav1, colNav2 = st.columns([0.5, 0.5])
with colNav1:
    if st.button("⬅️ Volver a 4 (Bottom-up)", key="back_to_4_from_5", use_container_width=True):
        st.switch_page("pages/04_Ventas_Botton_up.py")

with colNav2:
    if st.button("Siguiente ➡️ (Valoración)", key="next_step_5", disabled=not oblig_ok, use_container_width=True):
        reporte = {
            "modo": vin.get("modo"),
            "mes_referencia": mes_etiqueta,
            "mes_iso": mes_iso,
            "tiene_registros": vin.get("tiene_registros_compras") or vin.get("tiene_registros_fact"),
            "compras_mes_colones": int(vin.get("compras_mes") or 0),
            "tipo_margen": vin.get("tipo_margen"),
            "margen_pct": int(vin.get("margen_pct") or 0),
            "facturacion_bruta_mes_colones": int(vin.get("facturacion_bruta_mes") or 0),
            "comision_pct": int(vin.get("comision_pct") or 0),
            "ventas_reportadas_mes_colones": int(vin.get("ventas_reportadas_mes") or 0),
            "costo_pct_sobre_ventas": int(vin.get("costo_pct_sobre_ventas") or 0),
            "costo_estimado_colones": None,  # se calcula
            "ventas_estimadas_colones": None, # se calcula
            "comentario": vin.get("comentario").strip() if vin.get("comentario") else None,
            "no_data": 1 if st.session_state.no_data_p5 else 0
        }

        st.session_state.setdefault("reporte", {})
        st.session_state["reporte"]["ventas_p5"] = reporte
        st.session_state["done_05"] = True

        if cliente_id:
            ok = save_ventas_p5(cliente_id, reporte)
            if ok:
                st.success("Datos guardados en la base de datos.")
            else:
                st.error("No se pudieron guardar los datos en la base de datos.")

        try:
            st.switch_page("pages/06_Valoración_asesor.py")
        except Exception:
            st.success("Datos guardados. Abrí **06 – Valoración del asesor** desde el menú lateral.")
            st.stop()

