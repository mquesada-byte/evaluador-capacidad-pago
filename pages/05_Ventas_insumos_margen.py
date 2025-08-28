# pages/05_Ventas_insumos_margen.py
import streamlit as st
import datetime as dt
from zoneinfo import ZoneInfo

st.set_page_config(page_title="Paso 5: Ventas (insumos/margen)", page_icon="🧮")

TZ = ZoneInfo("America/Costa_Rica")

# =========================
# PASO 5 – Ventas (Insumos/Margen simple desde COMPRAS)
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

def init_paso5_state_simple():
    st.session_state.setdefault("ventas_insumos_simple", {})
    vin = st.session_state.ventas_insumos_simple
    vin.setdefault("tiene_registros", "Sí")        # "Sí" | "No"
    vin.setdefault("compras_mes", 0)               # ₡
    vin.setdefault("tipo_margen", "Sobre ventas")  # "Sobre ventas" | "Sobre compras (markup)"
    vin.setdefault("margen_pct", 30)               # % entero
    vin.setdefault("comentario", "")

def _calc_ventas_desde_compras_simple(compras: float, tipo_margen: str, margen_pct: float):
    m = max(0.0, float(margen_pct) / 100.0)
    if tipo_margen == "Sobre ventas":
        denom = 1.0 - m
        if denom <= 0:
            return None, "El margen sobre ventas debe ser menor a 100%."
        ventas = compras / denom
        return int(round(ventas)), None
    else:  # "Sobre compras (markup)"
        ventas = compras * (1.0 + m)
        return int(round(ventas)), None

# ---------- UI (multipágina; sin 'step') ----------
init_paso5_state_simple()
vin = st.session_state.ventas_insumos_simple

mes_etiqueta, mes_iso = _mes_anterior_label()  # p.ej. "julio 2025", "2025-07"
st.title("🧮 Paso 5: Ventas – Insumos/Margen (simple desde compras)")
st.caption(f"Mes de referencia: **{mes_etiqueta}**. Sin IVA ni mermas; aproximamos COGS ≈ Compras del mes.")

colR1, colR2 = st.columns([0.5, 0.5])
with colR1:
    vin["tiene_registros"] = st.radio(
        "¿Tiene facturas o registros de compras del mes?",
        options=["Sí", "No"],
        index=0 if vin["tiene_registros"] == "Sí" else 1,
        help="No es obligatorio para continuar, pero mejora la confiabilidad."
    )

vin["compras_mes"] = st.number_input(
    f"Compras del mes de {mes_etiqueta} (₡) *",
    min_value=0, step=1000, value=int(vin["compras_mes"]),
    help="Total pagado/por pagar a proveedores durante el mes de referencia."
)

st.markdown("---")

colM1, colM2 = st.columns([0.55, 0.45])
with colM1:
    vin["tipo_margen"] = st.radio(
        "¿El margen lo expresa sobre…?",
        options=["Sobre ventas", "Sobre compras (markup)"],
        index=0 if vin["tipo_margen"] == "Sobre ventas" else 1,
        help="Si dice 'gano 30% de lo que vendo' → Sobre ventas. Si dice 'vendo 50% más caro que el costo' → Sobre compras (markup)."
    )
with colM2:
    max_pct = 95 if vin["tipo_margen"] == "Sobre ventas" else 500
    vin["margen_pct"] = st.number_input(
        "Margen (%) *",
        min_value=0, max_value=max_pct, step=1, value=int(vin["margen_pct"]),
        help=("Debe ser < 100% si es sobre ventas." if vin["tipo_margen"] == "Sobre ventas"
              else "Puede ser >100% si es markup sobre compras (p. ej., 120%).")
    )

vin["comentario"] = st.text_area(
    "Comentario (opcional)",
    value=vin["comentario"],
    placeholder="Notas breves: compras extraordinarias para stock, cambios de precios, feriados, etc.",
    height=80
)

st.divider()

ventas_est, warn = _calc_ventas_desde_compras_simple(
    compras=float(vin["compras_mes"] or 0),
    tipo_margen=vin["tipo_margen"],
    margen_pct=float(vin["margen_pct"] or 0),
)

if warn:
    st.warning(warn)
elif ventas_est is not None and int(vin["compras_mes"]) > 0:
    st.info(f"**Ventas estimadas (Insumos/Margen) para {mes_etiqueta}:** ₡ {ventas_est:,}".replace(",", "."))

oblig_ok = (int(vin["compras_mes"]) > 0 and ventas_est is not None)

# --- Navegación ---
colNav1, colNav2 = st.columns([0.5, 0.5])
with colNav1:
    if st.button("⬅️ Volver a 4 (Bottom-up)", key="back_to_4_from_5", use_container_width=True):
        for prev_page in ["pages/04_Ventas_Botton_up.py", "pages/04_Ventas_botton_up.py"]:
            try:
                st.switch_page(prev_page)
                break
            except Exception:
                continue

with colNav2:
    if st.button(
        "Siguiente ➡️ (Valoración)",
        key="next_step_5_simple",
        disabled=not oblig_ok,
        use_container_width=True,
    ):
        st.session_state.setdefault("reporte", {})
        st.session_state["reporte"]["ventas_insumos_simple"] = {
            "mes_referencia": mes_etiqueta,
            "mes_iso": mes_iso,
            "tiene_registros_compras": vin["tiene_registros"],
            "compras_mes_colones": int(vin["compras_mes"]),
            "tipo_margen": vin["tipo_margen"],
            "margen_pct": int(vin["margen_pct"]),
            "ventas_estimadas_colones": int(ventas_est) if ventas_est is not None else None,
            "comentario": vin["comentario"].strip(),
            "supuesto_cogs_equivale_compras": True,
        }
        st.session_state["done_05"] = True

        # Ir a 06_Valoración_asesor.py (con fallback sin tilde)
        try:
            st.switch_page("pages/06_Valoración_asesor.py")
        except Exception:
            try:
                st.switch_page("pages/06_Valoracion_asesor.py")
            except Exception:
                st.success("Datos guardados. Abrí **06 – Valoración del asesor** desde el menú lateral.")
                st.stop()

