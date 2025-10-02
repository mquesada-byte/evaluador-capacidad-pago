# pages/04_Ventas_Botton_up.py
import streamlit as st
import datetime as dt
from zoneinfo import ZoneInfo

from utils.db import load_visita, save_ventas_bottomup  # 👈 importamos funciones de BD

st.set_page_config(page_title="Paso 4: Ventas Botton-up", page_icon="📊")

TZ = ZoneInfo("America/Costa_Rica")

# =========================
# PASO 4 – Ventas (Bottom-up / operativa)
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


def init_paso4_state(cliente_id: str, mes_iso: str):
    """Inicializa valores de session_state usando lo que haya en la BD."""
    st.session_state.setdefault("ventas_bottomup", {})
    st.session_state.setdefault("no_data", False)
    vbu = st.session_state.ventas_bottomup

    # Buscar registro existente en la BD
    datos = load_visita(cliente_id)
    if datos and "ventas_bottomup" in datos:
        db_row = datos["ventas_bottomup"]

        # 👇 Ahora carga siempre los datos, sin chequear mes_iso
        if db_row.get("no_data") == 1:
            st.session_state.no_data = True
        else:
            st.session_state.no_data = False

        vbu["unidad_clientes"] = db_row.get("unidad_clientes") or "Mes"
        vbu["clientes"] = db_row.get("clientes_valor") or 0
        vbu["dias_abiertos"] = db_row.get("dias_abiertos") or 0
        vbu["semanas_abiertas"] = db_row.get("semanas_abiertas") or 0
        vbu["ticket_promedio"] = db_row.get("ticket_promedio_colones") or 0
        vbu["comentario"] = db_row.get("comentario") or ""
    else:
        # Inicializar por defecto
        _init_defaults(vbu)



def _init_defaults(vbu: dict):
    vbu.setdefault("unidad_clientes", "Mes")
    vbu.setdefault("clientes", 0)
    vbu.setdefault("dias_abiertos", 0)
    vbu.setdefault("semanas_abiertas", 0)
    vbu.setdefault("ticket_promedio", 0)
    vbu.setdefault("comentario", "")


def _calc_bottom_up_total(vbu: dict) -> int:
    unidad = vbu.get("unidad_clientes", "Día")
    clientes = float(vbu.get("clientes") or 0)
    ticket = float(vbu.get("ticket_promedio") or 0)
    if unidad == "Día":
        dias = int(vbu.get("dias_abiertos") or 0)
        total = dias * clientes * ticket
    elif unidad == "Semana":
        semanas = int(vbu.get("semanas_abiertas") or 0)
        total = semanas * clientes * ticket
    else:  # "Mes"
        total = clientes * ticket
    return int(round(total))


# --------- UI ----------
mes_etiqueta, mes_iso = _mes_anterior_label()
cliente_id = st.session_state.get("cliente", {}).get("identificacion", "").strip()


init_paso4_state(cliente_id, mes_iso)
vbu = st.session_state.ventas_bottomup

st.title("📊 Paso 4: Ventas – Bottom-up (operativa)")
st.caption(f"Estimación del último mes calendario: **{mes_etiqueta}**.")

# Casilla "No tengo datos"
st.session_state.no_data = st.checkbox(
    "No tengo datos para este mes",
    value=st.session_state.no_data
)

# Deshabilitar entradas si está marcada
is_disabled = st.session_state.no_data

vbu["unidad_clientes"] = st.selectbox(
    "Clientes medidos por *",
    options=["Día", "Semana", "Mes"],
    index=["Día", "Semana", "Mes"].index(vbu["unidad_clientes"]) if vbu["unidad_clientes"] in ["Día", "Semana", "Mes"] else 0,
    help="Elija si los clientes que declarará son por día, por semana o por mes.",
    disabled=is_disabled
)

if vbu["unidad_clientes"] == "Día":
    col1, col2, col3 = st.columns([0.33, 0.33, 0.34])
    with col1:
        vbu["dias_abiertos"] = st.number_input("Días abiertos en el mes *", 0, 31, int(vbu["dias_abiertos"]), step=1, disabled=is_disabled)
    with col2:
        vbu["clientes"] = st.number_input("Clientes por día *", 0, 9999, int(vbu["clientes"]), step=1, disabled=is_disabled)
    with col3:
        vbu["ticket_promedio"] = st.number_input("Ticket promedio (₡/cliente) *", 0, 1_000_000, int(vbu["ticket_promedio"]), step=100, disabled=is_disabled)
elif vbu["unidad_clientes"] == "Semana":
    col1, col2, col3 = st.columns([0.33, 0.33, 0.34])
    with col1:
        vbu["semanas_abiertas"] = st.number_input("Semanas abiertas en el mes *", 0, 5, int(vbu["semanas_abiertas"]), step=1, disabled=is_disabled)
    with col2:
        vbu["clientes"] = st.number_input("Clientes por semana *", 0, 9999, int(vbu["clientes"]), step=1, disabled=is_disabled)
    with col3:
        vbu["ticket_promedio"] = st.number_input("Ticket promedio (₡/cliente) *", 0, 1_000_000, int(vbu["ticket_promedio"]), step=100, disabled=is_disabled)
else:  # "Mes"
    col1, col2 = st.columns([0.5, 0.5])
    with col1:
        vbu["clientes"] = st.number_input("Clientes en el mes *", 0, 999999, int(vbu["clientes"]), step=1, disabled=is_disabled)
    with col2:
        vbu["ticket_promedio"] = st.number_input("Ticket promedio (₡/cliente) *", 0, 1_000_000, int(vbu["ticket_promedio"]), step=100, disabled=is_disabled)

vbu["comentario"] = st.text_area(
    "Comentario (opcional)",
    value=vbu["comentario"],
    height=80,
    placeholder="Notas breves: cierres, feriados, eventos o cambios que afecten este cálculo.",
    disabled=is_disabled
)

st.divider()

# Cálculo
total_estimado = _calc_bottom_up_total(vbu)
st.info(f"**Ventas estimadas (Bottom-up) para {mes_etiqueta}: ₡ {total_estimado:,}**".replace(",", "."))

# Validación
if st.session_state.no_data:
    obligatorios_ok = True
else:
    if vbu["unidad_clientes"] == "Día":
        obligatorios_ok = (vbu["dias_abiertos"] > 0 and vbu["clientes"] > 0 and vbu["ticket_promedio"] > 0)
    elif vbu["unidad_clientes"] == "Semana":
        obligatorios_ok = (vbu["semanas_abiertas"] > 0 and vbu["clientes"] > 0 and vbu["ticket_promedio"] > 0)
    else:
        obligatorios_ok = (vbu["clientes"] > 0 and vbu["ticket_promedio"] > 0)

# Navegación
colNav1, colNav2 = st.columns([0.5, 0.5])
with colNav1:
    if st.button("⬅️ Volver a 3A (Top-down)", key="back_to_3A", use_container_width=True):
        st.switch_page("pages/03_Ventas_top_down.py")

with colNav2:
    if st.button("Siguiente ➡️ (5)", key="next_step_4", disabled=not obligatorios_ok, use_container_width=True):
        reporte = {
            "mes_referencia": mes_etiqueta,
            "mes_iso": mes_iso,
            "unidad_clientes": vbu.get("unidad_clientes"),
            "clientes_valor": int(vbu["clientes"]) if not st.session_state.no_data else None,
            "dias_abiertos": int(vbu["dias_abiertos"]) if vbu["unidad_clientes"] == "Día" and not st.session_state.no_data else None,
            "semanas_abiertas": int(vbu["semanas_abiertas"]) if vbu["unidad_clientes"] == "Semana" and not st.session_state.no_data else None,
            "ticket_promedio_colones": int(vbu["ticket_promedio"]) if not st.session_state.no_data else None,
            "ventas_estimadas_colones": int(total_estimado) if not st.session_state.no_data else None,
            "comentario": vbu["comentario"].strip() if vbu["comentario"] else None,
            "no_data": 1 if st.session_state.no_data else 0
        }
        st.session_state.setdefault("reporte", {})
        st.session_state["reporte"]["ventas_bottomup"] = reporte
        st.session_state["done_04"] = True

        if cliente_id:
            ok = save_ventas_bottomup(cliente_id, reporte)
            if ok:
                st.success("Datos guardados en la base de datos.")
            else:
                st.error("No se pudieron guardar los datos en la base de datos.")

        try:
            st.switch_page("pages/05_Ventas_insumos_margen.py")
        except Exception:
            st.success("Ventas Bottom-up guardadas. Abre el **Paso 5 – Ventas (insumos/margen)** desde el menú lateral.")
            st.stop()

