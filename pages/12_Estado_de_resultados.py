# ---------------------------------------------------------
# Lee st.session_state["reporte"] generado por los pasos previos
# y calcula el Disponible para pago del préstamo (Credimujer).
# No modifica los datos previos, solo los lee y resume.

import streamlit as st
import pandas as pd

st.set_page_config(page_title="Paso 12: Estado de Resultados", page_icon="📑")

# ========= Helpers de lectura/formatos =========
def _getr(path, default=None):
    """
    Lee un valor del reporte en session_state, navegando por una lista de claves.
    Ejemplo: _getr(["ventas_p5", "ventas_estimadas_colones"])
    """
    cur = st.session_state.get("reporte", {}) or {}
    try:
        for p in path:
            cur = cur[p]
        return cur
    except (KeyError, IndexError, TypeError):
        return default

def _num(x, default=0.0):
    """Convierte un valor a float de manera segura."""
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
    """Convierte un valor a float o retorna None."""
    try:
        if x is None or (isinstance(x, str) and x.strip() == ""):
            return None
        return float(str(x).strip().replace(",", "").replace("₡", ""))
    except Exception:
        return None

def _fmt_col(x):
    """Formatea un número como moneda de Costa Rica."""
    try:
        return f"₡{int(round(_num(x))):,}".replace(",", ".")
    except Exception:
        return "₡0"

# ========= Guardrail para datos faltantes =========
if "reporte" not in st.session_state or "ventas_p5" not in st.session_state["reporte"]:
    st.warning("¡Faltan datos de Ventas! Por favor, regresa al **Paso 5** para ingresar la información de ventas, compras y margen.")
    if st.button("⬅️ Volver a 5 – Ventas"):
        try:
            st.switch_page("pages/05_Ventas_insumos_margen.py")
        except Exception:
            st.stop()
    st.stop()
    
# ========= Recolección (con rutas de origen) =========
src = {}
vin = st.session_state["reporte"]["ventas_p5"]

# 1) Ventas - Se busca en múltiples lugares, priorizando Conciliación y luego el Paso 5
ventas_total = _getr(["ventas_conciliacion", "ventas_conciliadas_colones"])
if ventas_total:
    src["ventas"] = "reporte.ventas_conciliacion.ventas_conciliadas_colones"
else:
    ventas_total = (
        _getr(["ventas_p5", "ventas_estimadas_colones"]) or
        _getr(["ventas_topdown", "monto_colones"]) or
        _getr(["ventas_bottomup", "ventas_estimadas_colones"])
    )
    if ventas_total:
        if _getr(["ventas_p5", "ventas_estimadas_colones"]):
            src["ventas"] = "reporte.ventas_p5.ventas_estimadas_colones"
        elif _getr(["ventas_topdown", "monto_colones"]):
            src["ventas"] = "reporte.ventas_topdown.monto_colones"
        else:
            src["ventas"] = "reporte.ventas_bottomup.ventas_estimadas_colones"
ventas_total = _num(ventas_total, 0)

# 2) Compras/Costos (Corregido para buscar según el modo del Paso 5)
compras_total = 0.0
if vin["modo"] == "Bienes (insumos/margen)":
    compras_total = _getr(["ventas_p5", "compras_mes_colones"])
    src["compras"] = "reporte.ventas_p5.compras_mes_colones"
elif vin["modo"] == "Servicio con costo = % de ventas":
    compras_total = _getr(["ventas_p5", "costo_estimado_colones"])
    src["compras"] = "reporte.ventas_p5.costo_estimado_colones"
else:
    src["compras"] = "No aplica (modo Servicio por comisión)"
compras_total = _num(compras_total, 0)

# 3) Margen (tipo + % - Corregido para buscar en la clave "ventas_p5")
tipo_margen = None
margen_pct = None
if vin["modo"] == "Bienes (insumos/margen)":
    tipo_margen = _getr(["ventas_p5", "tipo_margen"])
    margen_pct = _num_or_none(_getr(["ventas_p5", "margen_pct"]))
    if tipo_margen is not None and margen_pct is not None:
        src["margen"] = "reporte.ventas_p5.(tipo_margen,margen_pct)"
elif vin["modo"] == "Servicio por comisión (%)":
    tipo_margen = "Sobre facturación bruta"
    margen_pct = _num_or_none(_getr(["ventas_p5", "comision_pct"]))
    if tipo_margen is not None and margen_pct is not None:
        src["margen"] = "reporte.ventas_p5.comision_pct"
elif vin["modo"] == "Servicio con costo = % de ventas":
    tipo_margen = "Costo directo"
    margen_pct = _num_or_none(_getr(["ventas_p5", "costo_pct_sobre_ventas"]))
    if tipo_margen is not None and margen_pct is not None:
        src["margen"] = "reporte.ventas_p5.costo_pct_sobre_ventas"


# 4) Gastos operativos
gastos_ope_total = _num(
    _getr(["gastos_operativos", "totales", "total_gasto_operativo_mensualizado_colones"], 0), 0
)
src["gastos_operativos"] = "reporte.gastos_operativos.totales.total_gasto_operativo_mensualizado_colones"

# 5) Otros ingresos (ajustado)
otros_ing_total = _getr(["otros_ingresos", "totales", "total_ponderado"])
ruta_oi = "reporte.otros_ingresos.totales.total_ponderado"
if not otros_ing_total:
    otros_ing_total = _getr(["otros_ingresos", "totales", "total_mensualizado"], 0)
    ruta_oi = "reporte.otros_ingresos.totales.total_mensualizado"
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

# ========= Cálculos ========= (ajustado)
no_data_flag = _getr(["ventas_p5", "no_data"], 0)

if no_data_flag == 1:  # Casilla "No tengo datos" marcada
    compras_total = 0
    utilidad_bruta = ventas_total
    tipo_margen = "Sin datos"
    margen_pct = 0
else:
    # Compras/Costos
    compras_total = 0.0
    if vin["modo"] == "Bienes (insumos/margen)":
        compras_total = _getr(["ventas_p5", "compras_mes_colones"])
        src["compras"] = "reporte.ventas_p5.compras_mes_colones"
    elif vin["modo"] == "Servicio con costo = % de ventas":
        compras_total = _getr(["ventas_p5", "costo_estimado_colones"])
        src["compras"] = "reporte.ventas_p5.costo_estimado_colones"
    else:
        src["compras"] = "No aplica (modo Servicio por comisión)"
    compras_total = _num(compras_total, 0)

    # Utilidad Bruta según margen
    utilidad_bruta = ventas_total - compras_total
    if (margen_pct is not None) and (tipo_margen in ("Sobre ventas", "Sobre compras (markup)", "Sobre facturación bruta", "Costo directo")):
        if tipo_margen == "Costo directo":
            utilidad_bruta = ventas_total - compras_total
        else:
            pct = margen_pct / 100.0
            if tipo_margen in ("Sobre ventas", "Sobre facturación bruta"):
                utilidad_bruta = ventas_total * pct
            elif tipo_margen == "Sobre compras (markup)":
                utilidad_bruta = compras_total * pct

# Continuar con el flujo
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
    base_txt = "—"
    if tipo_margen == "Sobre ventas" or tipo_margen == "Sobre facturación bruta":
        base_txt = "ventas"
    elif tipo_margen == "Sobre compras (markup)":
        base_txt = "compras"
    elif tipo_margen == "Costo directo":
        base_txt = "ventas"

    if margen_pct is not None:
        st.metric(f"Margen ({tipo_margen})", f"{margen_pct:.0f}% sobre {base_txt}")
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
    if st.button(
        "Continuar ➡️ Balance general",
        type="primary",
        use_container_width=True,
    ):
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
