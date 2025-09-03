# pages/05_Ventas_insumos_margen.py
import streamlit as st
import datetime as dt
from zoneinfo import ZoneInfo

st.set_page_config(page_title="Paso 5: Ventas (insumos/margen, comisión o costo % ventas)", page_icon="🧮")

TZ = ZoneInfo("America/Costa_Rica")

# =========================
# Utilidades
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

def _fmt_crc(n):
    return f"₡ {int(round(n)):,}".replace(",", ".")

# =========================
# Estado inicial
# =========================
def init_paso5_state():
    st.session_state.setdefault("ventas_p5", {})
    vin = st.session_state.ventas_p5

    # Modo de cálculo:
    # 1) Bienes (insumos/margen)
    # 2) Servicio por comisión (% sobre facturación bruta)
    # 3) Servicio con costo = % de ventas (ingresos directos)
    vin.setdefault("modo", "Bienes (insumos/margen)")

    # --- 1) Bienes ---
    vin.setdefault("tiene_registros_compras", "Sí")      # "Sí" | "No"
    vin.setdefault("compras_mes", 0)                      # ₡
    vin.setdefault("tipo_margen", "Sobre ventas")        # "Sobre ventas" | "Sobre compras (markup)"
    vin.setdefault("margen_pct", 30)                      # %

    # --- 2) Servicio por comisión ---
    vin.setdefault("tiene_registros_fact", "Sí")        # "Sí" | "No"
    vin.setdefault("facturacion_bruta_mes", 0)           # ₡ facturado al cliente final
    vin.setdefault("comision_pct", 10)                   # %

    # --- 3) Servicio con costo = % de ventas ---
    vin.setdefault("ventas_reportadas_mes", 0)           # ₡ ventas/ingresos directos del negocio
    vin.setdefault("costo_pct_sobre_ventas", 10)         # % del costo (transporte/otros) sobre ventas

    vin.setdefault("comentario", "")
    st.session_state.setdefault("no_data_p5", False) # Nueva variable de estado para la casilla

# =========================
# Cálculos
# =========================
def _calc_ventas_bienes_desde_compras(compras: float, tipo_margen: str, margen_pct: float):
    """
    Bienes: aproximamos COGS ≈ Compras del mes.
    - Si margen 'Sobre ventas': Ventas = Compras / (1 - m)
    - Si margen 'Sobre compras (markup)': Ventas = Compras * (1 + m)
    """
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
    """
    Servicios por comisión: Ingreso del negocio = facturación bruta * % comisión.
    """
    m = max(0.0, float(comision_pct) / 100.0)
    if m > 1.0:
        return None, "La comisión no puede superar 100%."
    ventas = fact_bruta * m
    return ventas, None

def _calc_servicio_costo_pct_ventas(ventas: float, costo_pct: float):
    """
    Servicio con costo = % de ventas: el asesor digita las ventas/ingresos del mes.
    Guardamos además el costo_estimado = ventas * costo_pct.
    """
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
init_paso5_state()
vin = st.session_state.ventas_p5
mes_etiqueta, mes_iso = _mes_anterior_label()
oblig_ok = False # Inicializa la variable de validación

st.title("🧮 Paso 5: Ventas")
st.caption(f"Mes de referencia: **{mes_etiqueta}**.")

# Opciones "No tengo datos" para deshabilitar los campos
st.session_state.no_data_p5 = st.checkbox(
    "No tengo datos para este mes",
    value=st.session_state.no_data_p5
)

is_disabled = st.session_state.no_data_p5

# Selector de modo
vin["modo"] = st.selectbox(
    "¿Cómo obtiene ingresos el negocio?",
    options=[
        "Bienes (insumos/margen)",
        "Servicio por comisión (%)",
        "Servicio con costo = % de ventas",
    ],
    index=["Bienes (insumos/margen)", "Servicio por comisión (%)", "Servicio con costo = % de ventas"].index(vin["modo"]),
    help=(
        "• Bienes: estima ventas desde compras + margen. "
        "• Comisión: ingreso = facturación bruta × % comisión. "
        "• Costo % ventas: se ingresan ventas y el costo directo como % de esas ventas."
    ),
    disabled=is_disabled
)

st.markdown("---")

# ---------------- 1) BIENES ----------------
if vin["modo"] == "Bienes (insumos/margen)":
    colR1, colR2 = st.columns([0.5, 0.5])
    with colR1:
        vin["tiene_registros_compras"] = st.radio(
            "¿Tiene facturas o registros de compras del mes?",
            options=["Sí", "No"],
            index=0 if vin["tiene_registros_compras"] == "Sí" else 1,
            help="No es obligatorio, pero mejora la confiabilidad.",
            disabled=is_disabled
        )

    vin["compras_mes"] = st.number_input(
        f"Compras del mes de {mes_etiqueta} (₡) *",
        min_value=0, step=1000, value=int(vin["compras_mes"]),
        help="Total pagado/por pagar a proveedores durante el mes (aprox. COGS).",
        disabled=is_disabled
    )

    st.markdown("---")
    colM1, colM2 = st.columns([0.55, 0.45])
    with colM1:
        vin["tipo_margen"] = st.radio(
            "¿El margen lo expresa sobre…?",
            options=["Sobre ventas", "Sobre compras (markup)"],
            index=0 if vin["tipo_margen"] == "Sobre ventas" else 1,
            help=("Si dice 'gano 30% de lo que vendo' → Sobre ventas. "
                  "Si dice 'vendo 50% más caro que el costo' → Sobre compras (markup)."),
            disabled=is_disabled
        )
    with colM2:
        max_pct = 95 if vin["tipo_margen"] == "Sobre ventas" else 500
        vin["margen_pct"] = st.number_input(
            "Margen (%) *",
            min_value=0, max_value=max_pct, step=1, value=int(vin["margen_pct"]),
            help=("Debe ser < 100% si es sobre ventas; puede ser >100% si es markup sobre compras."),
            disabled=is_disabled
        )

    vin["comentario"] = st.text_area(
        "Comentario (opcional)",
        value=vin["comentario"],
        placeholder="Notas: compras para stock, cambios de precios, feriados, etc.",
        height=80,
        disabled=is_disabled
    )

    ventas_est, warn = _calc_ventas_bienes_desde_compras(
        compras=float(vin["compras_mes"] or 0),
        tipo_margen=vin["tipo_margen"],
        margen_pct=float(vin["margen_pct"] or 0),
    )

    if warn:
        st.warning(warn)
    elif ventas_est is not None and int(vin["compras_mes"]) > 0:
        st.info(f"**Ventas estimadas (Bienes) {mes_etiqueta}:** {_fmt_crc(ventas_est)}")

    oblig_ok = (int(vin["compras_mes"]) > 0 and ventas_est is not None)

# ---------------- 2) SERVICIO POR COMISIÓN ----------------
elif vin["modo"] == "Servicio por comisión (%)":
    colR1, colR2 = st.columns([0.5, 0.5])
    with colR1:
        vin["tiene_registros_fact"] = st.radio(
            "¿Tiene registros de facturación/ingresos del mes?",
            options=["Sí", "No"],
            index=0 if vin["tiene_registros_fact"] == "Sí" else 1,
            help="Factura o total cobrado a los clientes por el servicio en el mes.",
            disabled=is_disabled
        )
    with colR2:
        vin["comision_pct"] = st.number_input(
            "Comisión que gana el negocio (%) *",
            min_value=0, max_value=100, step=1, value=int(vin["comision_pct"]),
            help="Ej.: 10% por administración del servicio.",
            disabled=is_disabled
        )

    vin["facturacion_bruta_mes"] = st.number_input(
        f"Facturación bruta del servicio en {mes_etiqueta} (₡) *",
        min_value=0, step=1000, value=int(vin["facturacion_bruta_mes"]),
        help="Total cobrado al cliente final por el servicio (base de cálculo de la comisión).",
        disabled=is_disabled
    )

    vin["comentario"] = st.text_area(
        "Comentario (opcional)",
        value=vin["comentario"],
        placeholder="Notas: contratos especiales, descuentos, comisiones variables, etc.",
        height=80,
        disabled=is_disabled
    )

    ventas_est, warn = _calc_ventas_servicio_comision(
        fact_bruta=float(vin["facturacion_bruta_mes"] or 0),
        comision_pct=float(vin["comision_pct"] or 0),
    )

    if warn:
        st.warning(warn)
    elif ventas_est is not None and int(vin["facturacion_bruta_mes"]) > 0:
        st.info(f"**Ventas estimadas (Servicio por comisión) {mes_etiqueta}:** {_fmt_crc(ventas_est)}")

    oblig_ok = (int(vin["facturacion_bruta_mes"]) > 0 and ventas_est is not None)

# ---------------- 3) SERVICIO CON COSTO = % DE VENTAS ----------------
else:
    st.markdown("**Este modo es ideal para servicios donde el negocio recibe el ingreso completo y sus costos directos son un % de esas ventas (p. ej., transporte, insumos menores).**")

    vin["ventas_reportadas_mes"] = st.number_input(
        f"Ventas/Ingresos reportados del mes {mes_etiqueta} (₡) *",
        min_value=0, step=1000, value=int(vin["ventas_reportadas_mes"]),
        help="Monto total que ingresa al negocio por el servicio en el mes.",
        disabled=is_disabled
    )

    vin["costo_pct_sobre_ventas"] = st.number_input(
        "Costo directo como % de las ventas *",
        min_value=0, max_value=100, step=1, value=int(vin["costo_pct_sobre_ventas"]),
        help="Ej.: 10% (transporte y otros).",
        disabled=is_disabled
    )

    vin["comentario"] = st.text_area(
        "Comentario (opcional)",
        value=vin["comentario"],
        placeholder="Notas: variaciones puntuales, contratos especiales, etc.",
        height=80,
        disabled=is_disabled
    )

    ventas_est, costo_estimado, warn = _calc_servicio_costo_pct_ventas(
        ventas=float(vin["ventas_reportadas_mes"] or 0),
        costo_pct=float(vin["costo_pct_sobre_ventas"] or 0),
    )

    if warn:
        st.warning(warn)
    elif ventas_est is not None and ventas_est > 0:
        st.info(
            f"**Ventas registradas {mes_etiqueta}:** {_fmt_crc(ventas_est)}  \n"
            f"**Costo directo estimado ({vin['costo_pct_sobre_ventas']}%):** {_fmt_crc(costo_estimado)}"
        )

    # Definir la validación de obligatorios para este modo
    oblig_ok = (int(vin["ventas_reportadas_mes"]) > 0 and ventas_est is not None)

# =========================
# Navegación
# =========================
# La validación final ahora considera la casilla "No hay datos"
if st.session_state.no_data_p5:
    oblig_ok = True

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
        if vin["modo"] == "Bienes (insumos/margen)":
            st.session_state["reporte"]["ventas_p5"] = {
                "modo": vin["modo"],
                "mes_referencia": mes_etiqueta,
                "mes_iso": mes_iso,
                "tiene_registros": vin["tiene_registros_compras"],
                "compras_mes_colones": int(vin["compras_mes"]),
                "tipo_margen": vin["tipo_margen"],
                "margen_pct": int(vin["margen_pct"]),
                "ventas_estimadas_colones": int(round(ventas_est)) if ventas_est is not None else None,
                "comentario": vin["comentario"].strip(),
                "supuesto_cogs_equivale_compras": True,
            }
        elif vin["modo"] == "Servicio por comisión (%)":
            st.session_state["reporte"]["ventas_p5"] = {
                "modo": vin["modo"],
                "mes_referencia": mes_etiqueta,
                "mes_iso": mes_iso,
                "tiene_registros_fact": vin["tiene_registros_fact"],
                "facturacion_bruta_mes_colones": int(vin["facturacion_bruta_mes"]),
                "comision_pct": int(vin["comision_pct"]),
                "ventas_estimadas_colones": int(round(ventas_est)) if ventas_est is not None else None,
                "comentario": vin["comentario"].strip(),
            }
        else:  # Servicio con costo = % de ventas
            st.session_state["reporte"]["ventas_p5"] = {
                "modo": vin["modo"],
                "mes_referencia": mes_etiqueta,
                "mes_iso": mes_iso,
                "ventas_reportadas_mes_colones": int(vin["ventas_reportadas_mes"]),
                "costo_pct_sobre_ventas": int(vin["costo_pct_sobre_ventas"]),
                "costo_estimado_colones": int(round(costo_estimado)) if costo_estimado is not None else None,
                "ventas_estimadas_colones": int(round(ventas_est)) if ventas_est is not None else None,
                "comentario": vin["comentario"].strip(),
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
