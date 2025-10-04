# pages/05_Ventas_insumos_margen.py
import streamlit as st
import datetime as dt
from zoneinfo import ZoneInfo

from utils.db import load_visita, save_ventas_p5

st.set_page_config(
    page_title="Paso 5: Ventas (insumos/margen, comisión o costo % ventas)",
    page_icon="🧮"
)

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
    meses_es = [
        "enero","febrero","marzo","abril","mayo","junio",
        "julio","agosto","septiembre","octubre","noviembre","diciembre"
    ]
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

        # 👇 Antes se validaba mes_iso, ahora siempre se cargan los datos
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
    vin.setdefault("tiene_registros", "Sí")
    vin.setdefault("compras_mes_colones", 0)
    vin.setdefault("tipo_margen", "Sobre ventas")
    vin.setdefault("margen_pct", 30)
    vin.setdefault("facturacion_bruta_mes_colones", 0)
    vin.setdefault("comision_pct", 10)
    vin.setdefault("ventas_reportadas_mes_colones", 0)
    vin.setdefault("costo_pct_sobre_ventas", 10)
    vin.setdefault("comentario", "")
    vin.setdefault("ventas_estimadas_colones", 0)
    vin.setdefault("costo_estimado_colones", 0)

# =========================
# Cálculos
# =========================
def _calc_ventas_bienes_desde_compras(compras: float, tipo_margen: str, margen_pct: float):
    m = max(0.0, float(margen_pct) / 100.0)
    if tipo_margen == "Sobre ventas":
        denom = 1.0 - m
        if denom <= 0:
            return None, "El margen sobre ventas debe ser menor a 100%."
        ventas = compras / denom
        return ventas, None
    else:  # "Sobre compras (markup)"
        ventas = compras * (1.0 + m)
        return ventas, None

def _calc_ventas_servicio_comision(fact_bruta: float, comision_pct: float):
    m = max(0.0, float(comision_pct) / 100.0)
    if m > 1.0:
        return None, "La comisión no puede superar 100%."
    ventas = fact_bruta * m
    return ventas, None

def _calc_servicio_costo_pct_ventas(ventas: float, costo_pct: float):
    if ventas <= 0:
        return None, None, "Las ventas deben ser mayores a 0."
    m = max(0.0, float(costo_pct) / 100.0)
    if m > 1.0:
        return None, None, "El costo sobre ventas no puede superar 100%."
    costo_estimado = ventas * m
    return ventas, costo_estimado, None

# =========================
# UI
# =========================
mes_etiqueta, mes_iso = _mes_anterior_label()
cliente_id = st.session_state.get("cliente", {}).get("identificacion")

init_paso5_state(cliente_id, mes_iso)
vin = st.session_state.ventas_p5

# Inicializar validación
oblig_ok = False

st.title("🧮 Paso 5: Ventas")
st.caption(f"Mes de referencia: **{mes_etiqueta}**.")

st.session_state.no_data_p5 = st.checkbox(
    "No tengo datos para este mes",
    value=st.session_state.no_data_p5
)
is_disabled = st.session_state.no_data_p5

# 🔄 Si se marca "No tengo datos", limpiar los valores visibles inmediatamente
if st.session_state.no_data_p5:
    vin.update({
        "compras_mes_colones": 0,
        "margen_pct": 0,
        "facturacion_bruta_mes_colones": 0,
        "comision_pct": 0,
        "ventas_reportadas_mes_colones": 0,
        "costo_pct_sobre_ventas": 0,
        "costo_estimado_colones": 0,
        "ventas_estimadas_colones": 0,
        "comentario": "",
    })

# 🧭 Si el usuario vuelve a desmarcar "No tengo datos", restaurar valores por defecto
else:
    vin.setdefault("modo", "Bienes (insumos/margen)")
    vin.setdefault("tiene_registros", "Sí")
    vin.setdefault("compras_mes_colones", 0)
    vin.setdefault("tipo_margen", "Sobre ventas")
    vin.setdefault("margen_pct", 30)
    vin.setdefault("facturacion_bruta_mes_colones", 0)
    vin.setdefault("comision_pct", 10)
    vin.setdefault("ventas_reportadas_mes_colones", 0)
    vin.setdefault("costo_pct_sobre_ventas", 10)
    vin.setdefault("comentario", "")
    vin.setdefault("ventas_estimadas_colones", 0)
    vin.setdefault("costo_estimado_colones", 0)


# Selector de modo
vin["modo"] = st.selectbox(
    "¿Cómo obtiene ingresos el negocio?",
    options=[
        "Bienes (insumos/margen)",
        "Servicio por comisión (%)",
        "Servicio con costo = % de ventas",
    ],
    index=[
        "Bienes (insumos/margen)",
        "Servicio por comisión (%)",
        "Servicio con costo = % de ventas",
    ].index(vin["modo"]) if vin.get("modo") else 0,
    disabled=is_disabled
)

st.markdown("---")

# ---------------- 1) BIENES ----------------
if vin["modo"] == "Bienes (insumos/margen)":
    vin["tiene_registros"] = st.radio(
        "¿Tiene facturas o registros de compras del mes?",
        options=["Sí", "No"],
        index=0 if vin.get("tiene_registros") == "Sí" else 1,
        disabled=is_disabled
    )
    vin["compras_mes_colones"] = st.number_input(
        f"Compras del mes de {mes_etiqueta} (₡) *",
        min_value=0, step=1000, value=int(vin.get("compras_mes_colones") or 0),
        disabled=is_disabled
    )
    vin["tipo_margen"] = st.radio(
        "¿El margen lo expresa sobre…?",
        options=["Sobre ventas", "Sobre compras (markup)"],
        index=0 if vin.get("tipo_margen") == "Sobre ventas" else 1,
        disabled=is_disabled
    )
    vin["margen_pct"] = st.number_input(
        "Margen (%) *",
        min_value=0, max_value=500, step=1, value=int(vin.get("margen_pct") or 0),
        disabled=is_disabled
    )
    vin["comentario"] = st.text_area(
        "Comentario (opcional)",
        value=vin.get("comentario") or "",
        disabled=is_disabled
    )

    ventas_est, warn = _calc_ventas_bienes_desde_compras(
        compras=float(vin.get("compras_mes_colones") or 0),
        tipo_margen=vin.get("tipo_margen"),
        margen_pct=float(vin.get("margen_pct") or 0),
    )
    if warn:
        st.warning(warn)
    elif ventas_est is not None and int(vin.get("compras_mes_colones") or 0) > 0:
        st.info(f"**Ventas estimadas (Bienes) {mes_etiqueta}:** {_fmt_crc(ventas_est)}")
        vin["ventas_estimadas_colones"] = int(ventas_est)
    oblig_ok = (int(vin.get("compras_mes_colones") or 0) > 0 and ventas_est is not None)

# ---------------- 2) SERVICIO POR COMISIÓN ----------------
elif vin["modo"] == "Servicio por comisión (%)":
    vin["tiene_registros"] = st.radio(
        "¿Tiene registros de facturación/ingresos del mes?",
        options=["Sí", "No"],
        index=0 if vin.get("tiene_registros") == "Sí" else 1,
        disabled=is_disabled
    )
    vin["comision_pct"] = st.number_input(
        "Comisión (%) *",
        min_value=0, max_value=100, step=1, value=int(vin.get("comision_pct") or 0),
        disabled=is_disabled
    )
    vin["facturacion_bruta_mes_colones"] = st.number_input(
        f"Facturación bruta del servicio en {mes_etiqueta} (₡) *",
        min_value=0, step=1000, value=int(vin.get("facturacion_bruta_mes_colones") or 0),
        disabled=is_disabled
    )
    vin["comentario"] = st.text_area(
        "Comentario (opcional)",
        value=vin.get("comentario") or "",
        disabled=is_disabled
    )

    ventas_est, warn = _calc_ventas_servicio_comision(
        fact_bruta=float(vin.get("facturacion_bruta_mes_colones") or 0),
        comision_pct=float(vin.get("comision_pct") or 0),
    )
    if warn:
        st.warning(warn)
    elif ventas_est is not None and int(vin.get("facturacion_bruta_mes_colones") or 0) > 0:
        st.info(f"**Ventas estimadas (Servicio por comisión) {mes_etiqueta}:** {_fmt_crc(ventas_est)}")
        vin["ventas_estimadas_colones"] = int(ventas_est)
    oblig_ok = (int(vin.get("facturacion_bruta_mes_colones") or 0) > 0 and ventas_est is not None)

# ---------------- 3) SERVICIO COSTO % VENTAS ----------------
else:
    vin["ventas_reportadas_mes_colones"] = st.number_input(
        f"Ventas/Ingresos reportados {mes_etiqueta} (₡) *",
        min_value=0, step=1000, value=int(vin.get("ventas_reportadas_mes_colones") or 0),
        disabled=is_disabled
    )
    vin["costo_pct_sobre_ventas"] = st.number_input(
        "Costo directo como % de ventas *",
        min_value=0, max_value=100, step=1, value=int(vin.get("costo_pct_sobre_ventas") or 0),
        disabled=is_disabled
    )
    vin["comentario"] = st.text_area(
        "Comentario (opcional)",
        value=vin.get("comentario") or "",
        disabled=is_disabled
    )

    ventas_est, costo_estimado, warn = _calc_servicio_costo_pct_ventas(
        ventas=float(vin.get("ventas_reportadas_mes_colones") or 0),
        costo_pct=float(vin.get("costo_pct_sobre_ventas") or 0),
    )
    if warn:
        st.warning(warn)
    elif ventas_est is not None and ventas_est > 0:
        st.info(
            f"**Ventas registradas {mes_etiqueta}:** {_fmt_crc(ventas_est)}  \n"
            f"**Costo directo estimado ({vin['costo_pct_sobre_ventas']}%):** {_fmt_crc(costo_estimado)}"
        )
        vin["ventas_estimadas_colones"] = int(ventas_est)
        vin["costo_estimado_colones"] = int(costo_estimado)
    oblig_ok = (int(vin.get("ventas_reportadas_mes_colones") or 0) > 0 and ventas_est is not None)

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

        # 🔒 Si NO HAY DATOS, limpiamos los valores en memoria para que la UI quede en cero al recargar,
        # y enviamos NULL a la BD (mismo comportamiento que el Paso 4)
        if st.session_state.no_data_p5:
            for k in (
                "compras_mes_colones", "margen_pct", "facturacion_bruta_mes_colones", "comision_pct",
                "ventas_reportadas_mes_colones", "costo_pct_sobre_ventas",
                "costo_estimado_colones", "ventas_estimadas_colones"
            ):
                vin[k] = 0  # UI en cero al recargar

        reporte = {
            "modo": vin.get("modo"),
            "mes_referencia": mes_etiqueta,
            "mes_iso": mes_iso,

            # 👉 Enviamos NULL cuando no_data_p5 = 1
            "tiene_registros": None if st.session_state.no_data_p5 else vin.get("tiene_registros"),
            "compras_mes_colones": None if st.session_state.no_data_p5 else int(vin.get("compras_mes_colones") or 0),
            "tipo_margen": vin.get("tipo_margen"),  # dejamos la clasificación (análoga a unidad_clientes del Paso 4)
            "margen_pct": None if st.session_state.no_data_p5 else int(vin.get("margen_pct") or 0),
            "facturacion_bruta_mes_colones": None if st.session_state.no_data_p5 else int(vin.get("facturacion_bruta_mes_colones") or 0),
            "comision_pct": None if st.session_state.no_data_p5 else int(vin.get("comision_pct") or 0),
            "ventas_reportadas_mes_colones": None if st.session_state.no_data_p5 else int(vin.get("ventas_reportadas_mes_colones") or 0),
            "costo_pct_sobre_ventas": None if st.session_state.no_data_p5 else int(vin.get("costo_pct_sobre_ventas") or 0),
            "costo_estimado_colones": None if st.session_state.no_data_p5 else int(vin.get("costo_estimado_colones") or 0),
            "ventas_estimadas_colones": None if st.session_state.no_data_p5 else int(vin.get("ventas_estimadas_colones") or 0),

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

