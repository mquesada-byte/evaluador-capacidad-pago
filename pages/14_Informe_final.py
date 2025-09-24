# pages/14_Informe_final.py
# ---------------------------------------------------------
# Informe final (portada + cliente/negocio + valoración + análisis de ventas)
# con botón para descargar en PDF.
#
# Requiere: reportlab (agregar a requirements.txt si no está disponible)

import io
import datetime as dt
from zoneinfo import ZoneInfo

import streamlit as st
import pandas as pd


# ---------- Sincronizar Balance General ----------
def _sync_balance_general():
    if "reporte" not in st.session_state:
        return
    rep = st.session_state["reporte"].setdefault("balance_general", {})

    # Mapear claves de session_state a balance_general
    mapping = {
        "bg_inv_mp": "inv_mp",
        "bg_inv_pp": "inv_pp",
        "bg_inv_pt": "inv_pt",
        "bg_cxc_clientes": "cxc_clientes",
        "bg_caja_bancos": "caja_bancos",
        "bg_cpp": "cpp",
        "bg_anticipos": "anticipos",
        "bg_activo_fijo": "activo_fijo",
        "bg_comentarios": "comentarios",
    }

    for state_key, rep_key in mapping.items():
        if state_key in st.session_state and st.session_state[state_key]:
            rep[rep_key] = st.session_state[state_key]


# Llamar la sincronización apenas carga el informe
_sync_balance_general()


# ---------- Config ----------
st.set_page_config(page_title="Paso 14: Informe final", page_icon="📑", layout="centered")
TZ = ZoneInfo("America/Costa_Rica")


# ---------- Helpers ----------
def _fmt_dt(x):
    """Devuelve fecha/hora CR 'dd/mm/YYYY HH:MM:SS' o None si no puede formatear."""
    try:
        if x is None:
            return None
        if isinstance(x, str):
            return x
        if hasattr(x, "tzinfo") and x.tzinfo is not None:
            x = x.astimezone(TZ)
        return dt.datetime.fromtimestamp(x.timestamp(), tz=TZ).strftime("%d/%m/%Y %H:%M:%S")
    except Exception:
        try:
            return dt.datetime.fromisoformat(str(x)).astimezone(TZ).strftime("%d/%m/%Y %H:%M:%S")
        except Exception:
            return None


def _parse_gps_str(s):
    try:
        if not s:
            return None, None
        parts = [p.strip() for p in str(s).split(",")]
        if len(parts) >= 2:
            return float(parts[0]), float(parts[1])
    except Exception:
        pass
    return None, None


def _maps_links(lat, lon):
    lat_s = f"{lat:.6f}"
    lon_s = f"{lon:.6f}"
    g = f"https://www.google.com/maps/search/?api=1&query={lat_s},{lon_s}"
    g_at = f"https://www.google.com/maps/@{lat_s},{lon_s},18z"
    osm = f"https://www.openstreetmap.org/?mlat={lat_s}&mlon={lon_s}#map=18/{lat_s}/{lon_s}"
    return g, g_at, osm


def _fmt_antiguedad(anios, meses):
    try:
        a = int(anios or 0)
        m = int(meses or 0)
        if a == 0 and m == 0:
            return ""
        return f"{a} año(s) y {m} mes(es)"
    except Exception:
        return ""


def _num(x):
    try:
        if x is None:
            return 0.0
        return float(str(x).replace(",", "").replace("₡", "").strip())
    except Exception:
        return 0.0


def _fmt_col(x):
    try:
        return f"₡ {int(round(_num(x))):,}".replace(",", ".")
    except Exception:
        return "₡ 0"


def _ajuste_tipicidad(valor, tipicidad):
    """Como 3A: Alto -10%, Bajo +10%, Típico sin ajuste."""
    if valor is None:
        return None, "—"
    v = _num(valor)
    if tipicidad == "Alto":
        return v * 0.90, "Alto → −10%"
    if tipicidad == "Bajo":
        return v * 1.10, "Bajo → +10%"
    return v, "Típico (sin ajuste)"


def _desv_pct(a, b):
    a, b = _num(a), _num(b)
    if a <= 0 or b <= 0:
        return None
    base = (a + b) / 2.0
    return abs(a - b) / base


def _precision_label(ape):
    if ape is None:
        return "Indefinida"
    if ape <= 0.20:
        return "Alta (≤20%)"
    if ape <= 0.40:
        return "Media (20–40%)"
    return "Baja (>40%)"

# --------------------------------------------------
# LECTURA DE DATOS DESDE LA PAGINA ASESOR
# --------------------------------------------------

ases = st.session_state.get("asesor", {}) or {}
rep = st.session_state.get("reporte", {}) or {}
rep_ases = rep.get("asesor", {}) or {}

# Asesor
asesor_nombre = rep_ases.get("nombre") or ases.get("nombre") or "(sin registrar)"
fecha_str = rep_ases.get("fecha_hora") or _fmt_dt(ases.get("fecha_hora")) or dt.datetime.now(TZ).strftime("%d/%m/%Y %H:%M:%S")
fuente_hora = rep_ases.get("hora_fuente") or (
    "Internet" if ases.get("timestamp_source") == "internet"
    else ("Dispositivo" if ases.get("timestamp_source") else "—")
)

# GPS
lat = ases.get("lat")
lon = ases.get("lon")
if lat is None or lon is None:
    lat, lon = _parse_gps_str(rep_ases.get("gps"))
gmap = rep_ases.get("google_maps")
gview = rep_ases.get("google_maps_vista")
osm = rep_ases.get("openstreetmap")
if (not gmap or not osm) and (lat is not None and lon is not None):
    gmap_gen, gview_gen, osm_gen = _maps_links(float(lat), float(lon))
    gmap = gmap or gmap_gen
    gview = gview or gview_gen
    osm = osm or osm_gen


# --------------------------------------------------
# CLIENTE / NEGOCIO
# --------------------------------------------------

cn = rep.get("cliente_negocio", {}) or {}
cli_live = st.session_state.get("cliente", {}) or {}
neg_live = st.session_state.get("negocio", {}) or {}

cliente_nombre = cn.get("cliente_nombre") or cli_live.get("nombre_completo") or "(sin registrar)"
cliente_cedula = cn.get("cliente_identificacion") or cli_live.get("identificacion") or "(sin registrar)"
nombre_comercial = cn.get("nombre_comercial") or neg_live.get("nombre_comercial") or "—"
sector = cn.get("sector_economico") or neg_live.get("sector_economico") or "—"
actividad = cn.get("actividad_principal") or neg_live.get("actividad_principal") or "—"
ubicacion = cn.get("ubicacion") or neg_live.get("ubicacion") or "—"
persona_juridica = cn.get("persona_juridica") or ("Sí" if neg_live.get("persona_juridica") else "No")
patente = cn.get("patente_municipal") or ("Sí" if neg_live.get("patente_municipal") else "No")
registros = cn.get("registros_contables") or ("Sí" if neg_live.get("registros_contables") else "No")
tipo_local = cn.get("tipo_local") or neg_live.get("tipo_local") or "—"
antiguedad = cn.get("antiguedad") or _fmt_antiguedad(
    neg_live.get("antiguedad_anios"),
    neg_live.get("antiguedad_meses")
) or "—"


# --------------------------------------------------
# VALORACION ASESOR
# --------------------------------------------------
val = rep.get("valoracion_asesor", {}) or st.session_state.get("valoracion_asesor", {}) or {}
conoc = int((val.get("conocimiento_0a10") or 0) if str(val.get("conocimiento_0a10") or "").strip() != "" else 0)
cred = int((val.get("credibilidad_0a10") or 0) if str(val.get("credibilidad_0a10") or "").strip() != "" else 0)
dudas = (val.get("dudas_declaracion") or "Sin dudas")
clas = (val.get("clasificacion") or "—")
factor_asesor = float(val.get("factor_asesor_0a1") or 0.0)
ev_raw = val.get("evidencia", [])
if isinstance(ev_raw, str):
    evidencia = [s.strip() for s in ev_raw.split(",") if s.strip()]
elif isinstance(ev_raw, list):
    evidencia = [str(x).strip() for x in ev_raw if str(x).strip()]
else:
    evidencia = []
coment_val = (val.get("comentario") or "").strip()


# --------------------------------------------------
# VENTAS
# --------------------------------------------------
vtd = rep.get("ventas_topdown", {}) or {}
top_raw = vtd.get("monto_colones")
tipicidad = vtd.get("tipicidad")
fuente_td = vtd.get("fuente")
conf_cli = vtd.get("confianza_cliente_0a10") or vtd.get("confianza_cliente")  # ✅ ajuste robusto
coment_td = (vtd.get("comentario") or "").strip()
top_ajustado, txt_ajuste = _ajuste_tipicidad(top_raw, tipicidad) if top_raw else (None, "—")

vbu = rep.get("ventas_bottomup", {}) or {}
bottom_val = vbu.get("ventas_estimadas_colones")
coment_bu = (vbu.get("comentario") or "").strip()

vin = rep.get("ventas_insumos_simple", rep.get("ventas_insumos", rep.get("ventas_p5", {}))) or {}  # ✅ ajuste robusto
insumos_val = None if vin.get("no_aplica") else vin.get("ventas_estimadas_colones")
coment_ins = (vin.get("comentario") or "").strip()

# Normalizamos el modo de insumos para mostrar en el informe
modo_insumos = vin.get("modo") or "Insumos/Margen"
if modo_insumos == "Bienes (insumos/margen)":
    insumos_decl = vin.get("compras_mes_colones")
elif modo_insumos == "Servicio por comisión (%)":
    insumos_decl = vin.get("facturacion_bruta_mes_colones")
elif modo_insumos == "Servicio con costo = % de ventas":
    insumos_decl = vin.get("ventas_reportadas_mes_colones")
else:
    insumos_decl = vin.get("ventas_estimadas_colones")

vcon = rep.get("ventas_conciliacion", {}) or {}
ventas_conc = vcon.get("ventas_conciliadas_colones")
max_dev = vcon.get("desviacion_max_pct")  # fracción 0–1 si existía
pesos = vcon.get("pesos", {}) or {}
estimaciones = vcon.get("estimaciones", [])


# ========= UI =========
st.title("📑 Informe final")
st.caption("Portada y resumen ejecutivo con datos consolidados de los pasos anteriores.")

# Portada / Encabezado
col1, col2 = st.columns([0.55, 0.45])
with col1:
    st.write(f"**Asesor:** {asesor_nombre}")
    st.write(f"**Fecha y hora de visita:** {fecha_str} ({fuente_hora})")
with col2:
    if isinstance(lat, (int, float)) and isinstance(lon, (int, float)):
        st.write(f"**GPS negocio:** {float(lat):.6f}, {float(lon):.6f}")
        links = []
        if gmap:
            links.append(f"[Google Maps]({gmap})")
        if gview:
            links.append(f"[Vista @18z]({gview})")
        if osm:
            links.append(f"[OpenStreetMap]({osm})")
        if links:
            st.markdown(" · ".join(links))
    else:
        st.info("GPS no disponible.")

st.subheader("👤 Cliente y negocio")
colL, colR = st.columns([0.55, 0.45], vertical_alignment="top")
with colL:
    st.markdown(
        f"""
**Cliente:** {cliente_nombre}  
**Identificación:** {cliente_cedula}  

**Nombre comercial:** {nombre_comercial}  
**Actividad principal:** {actividad}  
**Sector económico:** {sector}  
**Tipo de local:** {tipo_local}  
**Persona jurídica:** {persona_juridica}  
**Patente municipal:** {patente}  
**Registros contables:** {registros}  
**Antigüedad del negocio:** {antiguedad}
        """.strip()
    )
with colR:
    st.markdown("**Ubicación / señas del negocio**")
    st.info(ubicacion or "—")

st.subheader("III. Valoración del asesor de crédito")
colV1, colV2, colV3 = st.columns(3)
with colV1:
    st.metric("Conocimiento (0–10)", f"{conoc}")
with colV2:
    st.metric("Credibilidad (0–10)", f"{cred}")
with colV3:
    st.metric("Factor de confiabilidad", f"{factor_asesor:.2f}")

colV4, colV5 = st.columns(2)
with colV4:
    st.write(f"**Percepción de veracidad:** {dudas}")
with colV5:
    st.write(f"**Clasificación del caso:** {clas}")

st.markdown("**Evidencia observada:**")
if evidencia:
    st.markdown("\n".join([f"- {e}" for e in evidencia]))
else:
    st.caption("—")

st.markdown("**Comentario del asesor:**")
st.info(coment_val or "—")

# Análisis de ventas
st.subheader("III-b. Análisis de ventas")

filas = [
    {
        "Ángulo": "Top-down (clienta)",
        "Monto bruto": _fmt_col(top_raw),
        "Ajuste": txt_ajuste,
        "Usado": _fmt_col(top_ajustado),
    },
    {
        "Ángulo": "Bottom-up (operativa)",
        "Monto bruto": _fmt_col(bottom_val),
        "Ajuste": "—",
        "Usado": _fmt_col(bottom_val),
    },
    {
        "Ángulo": modo_insumos,
        "Monto bruto": _fmt_col(insumos_decl),
        "Ajuste": "—",
        "Usado": _fmt_col(insumos_val),
    },
]

st.dataframe(pd.DataFrame(filas), use_container_width=True, hide_index=True)



st.dataframe(pd.DataFrame(filas), use_container_width=True, hide_index=True)

ape = None
if ventas_conc:
    ventas_conc = _num(ventas_conc)
    if top_ajustado and ventas_conc > 0:
        ape = abs(_num(top_ajustado) - ventas_conc) / ventas_conc
    if max_dev is None:
        pares = []
        for a, b in [(top_ajustado, bottom_val), (top_ajustado, insumos_val), (bottom_val, insumos_val)]:
            d = _desv_pct(a, b)
            if d is not None:
                pares.append(d)
        max_dev = max(pares) if pares else None

    colS1, colS2, colS3 = st.columns(3)
    with colS1:
        st.metric("Ventas conciliadas", _fmt_col(ventas_conc))
    with colS2:
        st.metric("Precisión de la clienta", ("—" if ape is None else f"{(1-ape):.0%}"))
    with colS3:
        st.metric("Desviación máx. entre métodos", ("—" if max_dev is None else f"{max_dev:.0%}"))

    fuente_formal = fuente_td in ["Facturación electrónica", "POS/Datáfono", "Extractos bancarios/SINPE"]
    colQ1, colQ2, colQ3 = st.columns(3)
    with colQ1:
        st.write(f"**Fuente Top-down:** {fuente_td or '—'}")
        st.caption("Clasificación: " + ("Formal" if fuente_formal else ("—" if not fuente_td else "Informal")))
    with colQ2:
        st.write(f"**Confianza declarada por clienta:** {conf_cli if conf_cli is not None else '—'}/10")
    with colQ3:
        st.write(f"**Factor del asesor:** {f'{factor_asesor:.2f}' if factor_asesor else '—'}  ·  **Dudas:** {dudas or '—'}")

    if pesos:
        st.markdown(
            "**Ponderaciones en conciliación (Top/Bottom/Insumos):** "
            f"{pesos.get('top_down', 0):.2f} / {pesos.get('bottom_up', 0):.2f} / {pesos.get('insumos', 0):.2f}"
        )


# --------------------------------------------------
# COMENTARIOS ESPECIFICOS
# --------------------------------------------------
comentarios = []
if coment_td:
    comentarios.append(f"- Top-down (clienta): {coment_td}")
if coment_bu:
    comentarios.append(f"- Bottom-up: {coment_bu}")
if coment_ins:
    comentarios.append(f"- Insumos/Margen: {coment_ins}")
st.markdown("**Comentarios específicos de ventas:**")
st.markdown("\n".join(comentarios) if comentarios else "—")

st.divider()


# --------------------------------------------------
# ESTADO DE RESULTADOS (resumen)
# --------------------------------------------------

st.subheader("IV. Estado de Resultados")

er = st.session_state.get("reporte", {}).get("estado_resultados", {})

ventas_total = er.get("ventas_colones")
compras_total = er.get("compras_costos_colones")
utilidad_bruta = er.get("utilidad_bruta_colones")
gastos_ope_total = er.get("gastos_operativos_colones")
utilidad_neta_ope = er.get("utilidad_neta_operativa_colones")
otros_ing_total = er.get("otros_ingresos_colones")
subtotal_post_otros = er.get("subtotal_post_otros_colones")
gastos_fam_total = er.get("gastos_familiares_colones")
deudas_total = er.get("pago_de_deudas_colones")
disponible_final = er.get("disponible_para_prestamo_colones")

if er:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Ventas", _fmt_col(ventas_total))
    with col2:
        st.metric("Compras/Costos", _fmt_col(compras_total))
    with col3:
        st.metric("Utilidad Bruta", _fmt_col(utilidad_bruta))

    col4, col5 = st.columns(2)
    with col4:
        st.metric("🧾 Gastos Operativos", _fmt_col(gastos_ope_total))
    with col5:
        st.metric("📌 Utilidad Neta Operativa", _fmt_col(utilidad_neta_ope))

    st.markdown("---")
    col6, col7 = st.columns(2)
    with col6:
        st.metric("➕ Otros ingresos", _fmt_col(otros_ing_total))
    with col7:
        st.metric("Subtotal post-otros", _fmt_col(subtotal_post_otros))

    st.markdown("---")
    col8, col9 = st.columns(2)
    with col8:
        st.metric("👪 Gastos familiares", _fmt_col(gastos_fam_total))
    with col9:
        st.metric("💳 Pago de deudas", _fmt_col(deudas_total))

    st.success(f"💰 **Disponible para el préstamo:** {_fmt_col(disponible_final)}")
else:
    st.info("No se encontraron datos del Estado de Resultados (Paso 12).")


# --------------------------------------------------
# BALANCE GENERAL (resumen)
# --------------------------------------------------


st.subheader("V. Balance General")

bg = st.session_state.get("reporte", {}).get("balance_general", {})

tot = bg.get("totales", {}) or {}
comentarios_bg = bg.get("comentarios", "")

if tot:
    col1, col2 = st.columns(2)
    with col1:
        st.metric("💼 Activo Circulante", _fmt_col(tot.get("activo_circulante")))
        st.metric("🏭 Activo Fijo Neto", _fmt_col(tot.get("activo_fijo")))
        st.metric("🧮 Total Activos", _fmt_col(tot.get("total_activos")))
    with col2:
        st.metric("💳 Pasivo Circulante", _fmt_col(tot.get("pasivo_circulante")))
        st.metric("📉 Pasivo Largo Plazo", _fmt_col(tot.get("pasivo_largo")))
        st.metric("📉 Total Pasivos", _fmt_col(tot.get("total_pasivo")))

    st.markdown("---")
    col3, col4 = st.columns(2)
    with col3:
        st.metric("📈 Patrimonio (Activo - Pasivo)", _fmt_col(tot.get("patrimonio")))
    with col4:
        st.metric("🧰 Capital de trabajo (AC - PC)", _fmt_col(tot.get("capital_trabajo")))

    st.markdown("**Comentarios del asesor:**")
    st.info(comentarios_bg or "—")
else:
    st.info("No se encontraron datos del Balance General (Paso 13).")



# --------------------------------------------------
# PDF
# --------------------------------------------------

def _build_pdf_bytes() -> bytes:
    """Construye un PDF del informe usando reportlab y devuelve bytes."""
    try:
        from reportlab.lib.pagesizes import LETTER
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
        )
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors

        buf = io.BytesIO()
        doc = SimpleDocTemplate(
            buf,
            pagesize=LETTER,
            leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36
        )
        styles = getSampleStyleSheet()
        h1 = styles["Heading1"]; h1.fontSize = 16
        h2 = styles["Heading2"]; h2.spaceBefore = 12
        h3 = styles["Heading3"]; h3.spaceBefore = 8
        p  = styles["BodyText"]; p.leading = 14
        small = ParagraphStyle("small", parent=p, fontSize=9, leading=12, textColor=colors.grey)

        story = []

        # ----------------- Portada -----------------
        story.append(Paragraph("Informe de evaluación – Credimujer", h1))
        story.append(Paragraph(f"Fecha de visita: {fecha_str} ({fuente_hora})", p))
        story.append(Paragraph(f"Asesor: {asesor_nombre}", p))
        if isinstance(lat, (int, float)) and isinstance(lon, (int, float)):
            story.append(Paragraph(f"GPS: {float(lat):.6f}, {float(lon):.6f}", p))
        story.append(Spacer(1, 12))

        # ----------------- Cliente -----------------
        story.append(Paragraph("Cliente y negocio", h2))
        story.append(Paragraph(f"Cliente: {cliente_nombre}", p))
        story.append(Paragraph(f"Identificación: {cliente_cedula}", p))
        story.append(Paragraph(f"Nombre comercial: {nombre_comercial}", p))
        story.append(Paragraph(f"Actividad principal: {actividad}", p))
        story.append(Paragraph(f"Sector económico: {sector}", p))
        story.append(Paragraph(f"Tipo de local: {tipo_local}", p))
        story.append(Paragraph(f"Persona jurídica: {persona_juridica}", p))
        story.append(Paragraph(f"Patente municipal: {patente}", p))
        story.append(Paragraph(f"Registros contables: {registros}", p))
        story.append(Paragraph(f"Antigüedad del negocio: {antiguedad}", p))
        story.append(Paragraph(f"Ubicación / señas: {ubicacion}", p))
        story.append(Spacer(1, 8))

        # ----------------- Valoración -----------------
        story.append(Paragraph("Valoración del asesor", h2))
        t_val = Table(
            [["Conocimiento", "Credibilidad", "Factor", "Percepción", "Clasificación"],
             [str(conoc), str(cred), f"{factor_asesor:.2f}", dudas, clas]],
            colWidths=[90, 90, 90, 120, 120]
        )
        t_val.setStyle(TableStyle([
            ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
            ("BACKGROUND", (0,0), (-1,0), colors.whitesmoke),
            ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ]))
        story.append(t_val)
        if evidencia:
            story.append(Paragraph("Evidencia observada:", h3))
            for e in evidencia:
                story.append(Paragraph(f"• {e}", p))
        story.append(Paragraph("Comentario del asesor:", h3))
        story.append(Paragraph(coment_val or "—", p))

        story.append(PageBreak())

        # ----------------- Análisis de Ventas -----------------
        story.append(Paragraph("Análisis de ventas", h2))

        detalle_conc = vcon.get("detalle", {})

        data = [
            ["Ángulo", "Monto bruto", "Ajuste", "Usado"],
            ["Top-down (clienta)",
             _fmt_col(detalle_conc.get("top_down_raw")),
             detalle_conc.get("top_down_ajuste_txt", "—"),
             _fmt_col(detalle_conc.get("top_down_ajustado"))],
            ["Bottom-up (operativa)",
             _fmt_col(detalle_conc.get("bottom_up_raw")),
             "—",
             _fmt_col(detalle_conc.get("bottom_up_raw"))],
            [detalle_conc.get("insumos_modo", "Insumos/Margen"),
             _fmt_col(detalle_conc.get("insumos_declarado")),
             "—",
             _fmt_col(detalle_conc.get("insumos_estimado"))],
        ]

        t_sales = Table(data, colWidths=[150, 110, 120, 110])
        t_sales.setStyle(TableStyle([
            ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
            ("BACKGROUND", (0,0), (-1,0), colors.whitesmoke),
            ("ALIGN", (1,1), (-1,-1), "RIGHT"),
        ]))
        story.append(t_sales)
        story.append(Spacer(1, 6))

        # ----------------- Estado de Resultados -----------------
        story.append(Paragraph("Estado de Resultados", h2))
        er_data = [
            ["Ventas", _fmt_col(ventas_total)],
            ["Compras / Costos", _fmt_col(compras_total)],
            ["Utilidad Bruta", _fmt_col(utilidad_bruta)],
            ["Gastos Operativos", _fmt_col(gastos_ope_total)],
            ["Utilidad Neta Operativa", _fmt_col(utilidad_neta_ope)],
            ["Otros Ingresos", _fmt_col(otros_ing_total)],
            ["Subtotal post-otros", _fmt_col(subtotal_post_otros)],
            ["Gastos familiares", _fmt_col(gastos_fam_total)],
            ["Pago de deudas", _fmt_col(deudas_total)],
            ["Disponible para préstamo", _fmt_col(disponible_final)],
        ]
        t_er = Table(er_data, colWidths=[200, 200])
        t_er.setStyle(TableStyle([
            ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
            ("BACKGROUND", (0,0), (-1,0), colors.whitesmoke),
            ("ALIGN", (1,0), (-1,-1), "RIGHT"),
        ]))
        story.append(t_er)

        story.append(PageBreak())

        # ----------------- Balance General -----------------
        story.append(Paragraph("Balance General", h2))
        bg_data = [
            ["Activo Circulante", _fmt_col(tot.get("activo_circulante"))],
            ["Activo Fijo Neto", _fmt_col(tot.get("activo_fijo"))],
            ["Total Activos", _fmt_col(tot.get("total_activos"))],
            ["Pasivo Circulante", _fmt_col(tot.get("pasivo_circulante"))],
            ["Pasivo Largo Plazo", _fmt_col(tot.get("pasivo_largo"))],
            ["Total Pasivos", _fmt_col(tot.get("total_pasivo"))],
            ["Patrimonio", _fmt_col(tot.get("patrimonio"))],
            ["Capital de trabajo", _fmt_col(tot.get("capital_trabajo"))],
        ]
        t_bg = Table(bg_data, colWidths=[200, 200])
        t_bg.setStyle(TableStyle([
            ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
            ("BACKGROUND", (0,0), (-1,0), colors.whitesmoke),
            ("ALIGN", (1,0), (-1,-1), "RIGHT"),
        ]))
        story.append(t_bg)

        if comentarios_bg:
            story.append(Spacer(1, 6))
            story.append(Paragraph("Comentarios del Balance:", h3))
            story.append(Paragraph(comentarios_bg, p))

        doc.build(story)
        return buf.getvalue()

    except Exception as e:
        # Si hay error, devolvemos vacío sin cortar la app
        print(f"Error al generar PDF: {e}")
        return b""


# =============== Generar PDF y botones ===============
pdf_bytes = _build_pdf_bytes()
file_name = f"Informe_{cliente_nombre.replace(' ', '_')}.pdf"

if pdf_bytes:
    st.download_button(
        "💾 Descargar informe en PDF",
        data=pdf_bytes,
        file_name=file_name,
        mime="application/pdf",
        use_container_width=True,
        type="primary",
    )
else:
    st.info("No se pudo generar el PDF en este entorno. Verifica que `reportlab` esté instalado.")

st.divider()

# ================= Navegación =================
c1, c2, c3 = st.columns([0.33, 0.34, 0.33])

with c1:
    if st.button("⬅️ Volver a 13 – Balance General", use_container_width=True):
        for prev in ["pages/13_Balance_general.py", "13_Balance_general.py"]:
            try:
                st.switch_page(prev)
                break
            except Exception:
                continue

with c2:
    if st.button("Guardar y continuar ➡️", use_container_width=True):
        st.session_state["done_14"] = True
        for nxt in [
            "pages/15_Análisis_IA.py",
            "pages/15_Analisis_IA.py",
            "15_Analisis_IA.py",
        ]:
            try:
                st.switch_page(nxt)
                break
            except Exception:
                continue
        else:
            st.success("Informe final listo. Abrí **15 – Análisis IA** desde el menú lateral.")
            st.stop()

with c3:
    if st.button("Ir al inicio 🏠", use_container_width=True):
        try:
            st.switch_page("Home.py")
        except Exception:
            st.rerun()
