# pages/04_Ventas_Botton_up.py
import streamlit as st
import datetime as dt
from zoneinfo import ZoneInfo

st.set_page_config(page_title="Paso 4: Ventas Bottom-up", page_icon="📊")

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

def init_paso4_state():
    st.session_state.setdefault("ventas_bottomup", {})
    vbu = st.session_state.ventas_bottomup
    vbu.setdefault("unidad_clientes", "Día")     # "Día" | "Semana" | "Mes"
    vbu.setdefault("clientes", 0)                # clientes por unidad seleccionada
    vbu.setdefault("dias_abiertos", 0)           # si unidad = Día
    vbu.setdefault("semanas_abiertas", 4)        # si unidad = Semana
    vbu.setdefault("ticket_promedio", 0)         # ₡ por cliente
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

# --------- UI (multipágina; sin step) ----------
init_paso4_state()
vbu = st.session_state.ventas_bottomup

# Mes de referencia (del mes calendario anterior)
mes_etiqueta, mes_iso = _mes_anterior_label()

st.title("📊 Paso 4: Ventas – Bottom-up (operativa)")
st.caption(f"Estimación del último mes calendario: **{mes_etiqueta}**.")

# Unidad
vbu["unidad_clientes"] = st.selectbox(
    "Clientes medidos por *",
    options=["Día", "Semana", "Mes"],
    index=["Día", "Semana", "Mes"].index(vbu["unidad_clientes"]) if vbu["unidad_clientes"] in ["Día", "Semana", "Mes"] else 0,
    help="Elija si los clientes que declarará son por día, por semana o por mes."
)

# Entradas según la unidad
if vbu["unidad_clientes"] == "Día":
    col1, col2, col3 = st.columns([0.33, 0.33, 0.34])
    with col1:
        vbu["dias_abiertos"] = st.number_input(
            "Días abiertos en el mes *", min_value=0, max_value=31, step=1, value=int(vbu["dias_abiertos"]),
            help="Cantidad de días que operó el negocio en el mes de referencia."
        )
    with col2:
        vbu["clientes"] = st.number_input(
            "Clientes por día *", min_value=0, step=1, value=int(vbu["clientes"]),
            help="Promedio de clientes atendidos por día."
        )
    with col3:
        vbu["ticket_promedio"] = st.number_input(
            "Ticket promedio (₡/cliente) *", min_value=0, step=100, value=int(vbu["ticket_promedio"]),
            help="Venta promedio por cliente en colones."
        )
elif vbu["unidad_clientes"] == "Semana":
    col1, col2, col3 = st.columns([0.33, 0.33, 0.34])
    with col1:
        vbu["semanas_abiertas"] = st.number_input(
            "Semanas abiertas en el mes *", min_value=0, max_value=5, step=1, value=int(vbu["semanas_abiertas"]),
            help="Número de semanas efectivas trabajadas en el mes (usualmente 4–5)."
        )
    with col2:
        vbu["clientes"] = st.number_input(
            "Clientes por semana *", min_value=0, step=1, value=int(vbu["clientes"]),
            help="Promedio de clientes atendidos por semana."
        )
    with col3:
        vbu["ticket_promedio"] = st.number_input(
            "Ticket promedio (₡/cliente) *", min_value=0, step=100, value=int(vbu["ticket_promedio"]),
            help="Venta promedio por cliente en colones."
        )
else:  # "Mes"
    col1, col2 = st.columns([0.5, 0.5])
    with col1:
        vbu["clientes"] = st.number_input(
            "Clientes en el mes *", min_value=0, step=1, value=int(vbu["clientes"]),
            help="Total de clientes atendidos en todo el mes."
        )
    with col2:
        vbu["ticket_promedio"] = st.number_input(
            "Ticket promedio (₡/cliente) *", min_value=0, step=100, value=int(vbu["ticket_promedio"]),
            help="Venta promedio por cliente en colones."
        )

vbu["comentario"] = st.text_area(
    "Comentario (opcional)",
    value=vbu["comentario"],
    placeholder="Notas breves: p. ej., cierres, feriados, eventos o cambios que afecten este cálculo.",
    height=80
)

st.divider()

# Cálculo y vista previa
total_estimado = _calc_bottom_up_total(vbu)
st.info(f"**Ventas estimadas (Bottom-up) para {mes_etiqueta}: ₡ {total_estimado:,}**".replace(",", "."))

# -------- Validación obligatorios --------
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
    if st.button("Siguiente ➡️ (3C)", key="next_step_4", disabled=not obligatorios_ok, use_container_width=True):
        # Guardar bloque de reporte Bottom-up
        st.session_state.setdefault("reporte", {})
        st.session_state["reporte"]["ventas_bottomup"] = {
            "mes_referencia": mes_etiqueta,
            "mes_iso": mes_iso,
            "unidad_clientes": vbu["unidad_clientes"],
            "clientes_valor": int(vbu["clientes"]),
            "dias_abiertos": int(vbu["dias_abiertos"]) if vbu["unidad_clientes"] == "Día" else None,
            "semanas_abiertas": int(vbu["semanas_abiertas"]) if vbu["unidad_clientes"] == "Semana" else None,
            "ticket_promedio_colones": int(vbu["ticket_promedio"]),
            "ventas_estimadas_colones": int(total_estimado),
            "comentario": vbu["comentario"].strip(),
        }
        st.session_state["done_04"] = True

        # Intentar abrir el siguiente paso (3C / Insumos y margen).
        # Ajusta el nombre real cuando lo tengas.
        next_candidates = [
            "pages/05_Ventas_insumos_simple.py",
            "pages/05_Insumos_y_margen.py",
            "pages/03C_Insumos_y_margen.py",
        ]
        for candidate in next_candidates:
            try:
                st.switch_page(candidate)
                break
            except Exception:
                continue
        else:
            st.success("Ventas Bottom-up guardadas. Abrí el **siguiente paso (3C)** desde el menú lateral.")
            st.stop()

