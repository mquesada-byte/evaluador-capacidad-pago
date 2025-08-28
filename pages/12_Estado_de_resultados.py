# pages/12_Estado_de_resultadosl.py
# ---------------------------------------------------------
# Lee st.session_state["reporte"] generado por los pasos previos
# y calcula el Disponible para pago del préstamo (Credimujer).
# No modifica los datos previos, solo los lee y resume.

import streamlit as st
import pandas as pd

st.set_page_config(page_title="Paso 12: Estado de Resultados", page_icon="📑")

# ========= Helpers de lectura/formatos =========
def _getr(path, default=None):
    cur = st.session_state.get("reporte", {}) or {}
    try:
        for p in path:
            cur = cur[p]
        return cur
    except Exception:
        return default

def _num(x, default=0.0):
    try:
        if x is None:
            return float(default)
        return float(x)
    except Exception:
        try:
            s = str(x).strip().replace(",", "").replace("₡", "")
            return float(s or default)
        except Exception:
            return float(default)

def _num_or_none(x):
    try:
        if x is None or (isinstance(x, str) and x.strip() == ""):
            return None
        return float(str(x).strip().replace(",", "").replace("₡", ""))
    except Exception:
        return None

def _fmt_col(x):
    try:
        return f"₡{int(round(_num(x))):,}".replace(",", ".")
    except Exception:
        return "₡0"

# ========= Recolección (con rutas de origen) =========
src = {}

# 1) Ventas
ventas_total = _getr(["ventas_conciliacion", "ventas_conciliadas_colones"])
if ventas_total:
    src["ventas"] = "reporte.ventas_conciliacion.ventas_conciliadas_colones"
else:
    ventas_total = (
        _getr(["ventas_topdown", "monto_colones"]) or
        _getr(["ventas_bottomup", "ventas_estimadas_colones"]) or
        _getr(["ventas_insumos_simple", "ventas_estimadas_colones"]) or
        _getr(["ventas_insumos", "ventas_estimadas_colones"])
    )
    if ventas_total:
        if _getr(["ventas_topdown", "monto_colones"]):
            src["ventas"] = "reporte.ventas_topdown.monto_colones"
        elif _getr(["ventas_bottomup", "ventas_estimadas_colones"]):
            src["ventas"] = "reporte.ventas_bottomup.ventas_estimadas_colones"
        else:
            src["ventas"] = "reporte.ventas_insumos_simple.ventas_estimadas_colones"
ventas_total = _num(ventas_total, 0)

# 2) Compras/Costos (de 3C simple)
compras_total = _getr(["ventas_insumos_simple", "compras_mes_colones"])
if compras_total is not None:
    src["compras"] = "reporte.ventas_insumos_simple.compras_mes_colones"
else:
    compras_total = 0.0
compras_total = _num(compras_total, 0)

# 3) Margen (tipo + % desde 3C simple)
tipo_margen = _getr(["ventas_insumos_simple", "tipo_margen"])
margen_pct_raw = _getr(["ventas_insumos_simple", "margen_pct"])
margen_pct = _num_or_none(margen_pct_raw)
if tipo_margen is not None and margen_pct is not None:
    src["margen"] = "reporte.ventas_insumos_simple.(tipo_margen,margen_pct)"

# 4) Gastos operativos
gastos_ope_total = _num(
    _getr(["gastos_operativos", "totales", "total_gasto_operativo_mensualizado_colones"], 0), 0
)
src["gastos_operativos"] = "reporte.gastos_operativos.totales.total_gasto_operativo_mensualizado_colones"

# 5) Otros ingresos
otros_ing_total = _getr(["otros_ingresos", "totales", "total_ponderado_colones"])
ruta_oi = "reporte.otros_ingresos.totales.total_ponderado_colones"
if not otros_ing_total:
    otros_ing_total = _getr(["otros_ingresos", "totales", "total_mensualizado_colones"], 0)
    ruta_oi = "reporte.otros_ingresos.totales.total_mensualizado_colones"
src["otros_ingresos"] = ruta_oi
otros_ing_total = _num(otros_ing_total, 0)

# 6) Gastos familiares
gastos_fam_total = _num(
    _getr(["gastos_familiares", "totales", "total_gastos_familiares_mensualizado_colones"], 0), 0
)
src["gastos_familiares"] = "reporte.gastos_familiares.totales.total_gastos_familiares_mensualizado_colones"

# 7) Pago de deudas
deudas_total = _num(_getr(["deudas_activas", "totales", "total_pago_mensual_colones"], 0), 0)
src["deudas"] = "reporte.deudas_activas.totales.total_pago_mensual_colones"

# ========= Cálculos =========
utilidad_bruta = None
if (margen_pct is not None) and (tipo_margen in ("Sobre ventas", "Sobre compras (markup)")):
    pct = margen_pct if margen_pct <= 1 else margen_pct / 100.0
    if tipo_margen == "Sobre ventas":
        utilidad_bruta = ventas_total * pct
    else:
        utilidad_bruta = compras_total * pct
if utilidad_bruta is None:
    utilidad_bruta = max(0.0, ventas_total - compras_total)

utilidad_neta_ope   = utilidad_bruta - gastos_ope_total
subtotal_post_otros = utilidad_neta_ope + otros_ing_total
disponible_final    = subtotal_post_otros - gastos_fam_total - deudas_total

# ========= UI =========
st.title("📑 Paso 12: Estado de Resultados")
st.caption("Resumen automático a partir de tus pasos previos.")

with st.expander("🔎 Origen de datos (rutas detectadas)"):
    st.json(src)

col1, col2, col3 = st.columns(3)
with col1: st.metric("Ventas", _fmt_col(ventas_total))
with col2: st.metric("Compras/Costos", _fmt_col(compras_total))
with col3:
    base_txt = ("ventas" if (tipo_margen == "Sobre ventas")
                else ("compras" if (tipo_margen == "Sobre compras (markup)") else "—"))
    if margen_pct is not None:
        pct_show = margen_pct if margen_pct <= 1 else (margen_pct / 100.0)
        st.metric("Margen (base)", f"{pct_show:.0%} sobre {base_txt}")
    else:
        st.metric("Margen (base)", "— sobre —")

st.divider()

col4, col5 = st.columns(2)
with col4: st.metric("🧮 Utilidad Bruta", _fmt_col(utilidad_bruta))
with col5: st.metric("🧾 Gastos Operativos", _fmt_col(gastos_ope_total))
st.metric("📌 Utilidad Neta Operativa", _fmt_col(utilidad_neta_ope))

st.divider()

col6, col7 = st.columns(2)
with col6: st.metric("➕ Otros ingresos", _fmt_col(otros_ing_total))
with col7: st.metric("Subtotal post-otros", _fmt_col(subtotal_post_otros))

st.divider()

col8, col9 = st.columns(2)
with col8: st.metric("👪 Gastos familiares", _fmt_col(gastos_fam_total))
with col9: st.metric("💳 Pago de deudas", _fmt_col(deudas_total))

st.success(f"💰 **Disponible para el préstamo:** {_fmt_col(disponible_final)}")

with st.expander("Ver tablas de origen (si están disponibles)"):
    rep = st.session_state.get("reporte", {})
    st.subheader("Otros ingresos")
    st.dataframe(pd.DataFrame(rep.get("otros_ingresos", {}).get("tabla", [])), use_container_width=True)
    st.subheader("Gastos operativos")
    st.dataframe(pd.DataFrame(rep.get("gastos_operativos", {}).get("tabla", [])), use_container_width=True)
    st.subheader("Gastos familiares")
    st.dataframe(pd.DataFrame(rep.get("gastos_familiares", {}).get("tabla", [])), use_container_width=True)
    st.subheader("Deudas activas")
    st.dataframe(pd.DataFrame(rep.get("deudas_activas", {}).get("tabla", [])), use_container_width=True)

# ====== Navegación ======
st.divider()
col_nav1, col_nav2 = st.columns([0.5, 0.5])

with col_nav1:
    if st.button("⬅️ Volver a 11 – Gastos familiares", use_container_width=True):
        for prev in ["pages/11_Gastos_familiares.py"]:
            try:
                st.switch_page(prev)
                break
            except Exception:
                continue

with col_nav2:
    if st.button("Continuar ➡️ Balance general", type="primary", use_container_width=True):
        st.session_state.setdefault("reporte", {})
        st.session_state["reporte"]["estado_resultados"] = {
            "ventas_colones": int(round(ventas_total)),
            "compras_costos_colones": int(round(compras_total)),
            "margen_tipo": (tipo_margen or ""),
            "margen_pct": float(margen_pct) if margen_pct is not None else None,
            "utilidad_bruta_colones": int(round(utilidad_bruta)),
            "gastos_operativos_colones": int(round(gastos_ope_total)),
            "utilidad_neta_operativa_colones": int(round(utilidad_neta_ope)),
            "otros_ingresos_colones": int(round(otros_ing_total)),
            "gastos_familiares_colones": int(round(gastos_fam_total)),
            "pago_de_deudas_colones": int(round(deudas_total)),
            "subtotal_post_otros_colones": int(round(subtotal_post_otros)),
            "disponible_para_prestamo_colones": int(round(disponible_final)),
        }
        st.session_state["done_12"] = True
        # -> Principal: 13_Balance_general.py
        for nxt in [
            "pages/13_Balance_general.py",  # principal
            "pages/balance_general.py",     # alternativas por si cambia el nombre
            "balance_general.py",
            "pages/13_Balance.py",
        ]:
            try:
                st.switch_page(nxt)
                break
            except Exception:
                continue
        else:
            st.success("Estado de resultados guardado. Abrí **Balance general** desde el menú lateral.")
            st.stop()

# Corta ejecución
st.stop()


