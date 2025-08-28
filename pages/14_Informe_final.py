# informe_portada.py — Etapa 1: Asesor, fecha/hora y GPS
import datetime as dt
from zoneinfo import ZoneInfo
import streamlit as st

# Evitar conflicto si otra página ya llamó set_page_config
if not st.session_state.get("_page_config_set"):
    st.set_page_config(page_title="Informe – Portada", page_icon="📑", layout="centered")
    st.session_state["_page_config_set"] = True

TZ = ZoneInfo("America/Costa_Rica")

# ---------- Helpers robustos ----------
def _fmt_dt(x):
    """Devuelve fecha/hora como 'dd/mm/YYYY HH:MM:SS' o None si no puede formatear."""
    try:
        if x is None:
            return None
        if isinstance(x, str):
            return x  # ya viene formateada desde el Paso 1 (reporte.asesor.fecha_hora)
        # datetime / pandas.Timestamp
        if hasattr(x, "tzinfo") and x.tzinfo is not None:
            x = x.astimezone(TZ)
        return dt.datetime.fromtimestamp(x.timestamp(), tz=TZ).strftime("%d/%m/%Y %H:%M:%S")
    except Exception:
        try:
            # último intento: parsear string ISO
            return dt.datetime.fromisoformat(str(x)).astimezone(TZ).strftime("%d/%m/%Y %H:%M:%S")
        except Exception:
            return None

def _parse_gps_str(s):
    """Convierte 'lat, lon' en (lat, lon) floats."""
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

# ---------- Lectura desde session_state ----------
ases = st.session_state.get("asesor", {}) or {}
rep_ases = (st.session_state.get("reporte", {}) or {}).get("asesor", {}) or {}

# Nombre del asesor
nombre = rep_ases.get("nombre") or ases.get("nombre") or "(sin registrar)"

# Fecha y hora de visita + fuente
fecha_str = rep_ases.get("fecha_hora")
if not fecha_str:
    fecha_str = _fmt_dt(ases.get("fecha_hora")) or dt.datetime.now(TZ).strftime("%d/%m/%Y %H:%M:%S")
fuente = rep_ases.get("hora_fuente") or (
    "Internet" if ases.get("timestamp_source") == "internet"
    else ("Dispositivo" if ases.get("timestamp_source") else "—")
)

# GPS (lat, lon)
lat = ases.get("lat"); lon = ases.get("lon")
if lat is None or lon is None:
    lat, lon = _parse_gps_str(rep_ases.get("gps"))

# Enlaces de mapa (preferir los guardados en reporte)
gmap = rep_ases.get("google_maps")
gview = rep_ases.get("google_maps_vista")
osm  = rep_ases.get("openstreetmap")
if (not gmap or not osm) and (lat is not None and lon is not None):
    gmap_gen, gview_gen, osm_gen = _maps_links(float(lat), float(lon))
    gmap = gmap or gmap_gen
    gview = gview or gview_gen
    osm = osm or osm_gen

# ---------- UI ----------
st.title("🧭 Encabezado de visita")
st.caption("Datos del **Paso 1**: asesor, fecha/hora y ubicación GPS del negocio.")

col1, col2 = st.columns([0.55, 0.45])
with col1:
    st.write(f"**Asesor:** {nombre}")
    st.write(f"**Fecha y hora de visita:** {fecha_str} ({fuente})")

with col2:
    if isinstance(lat, (int, float)) and isinstance(lon, (int, float)):
        st.write(f"**GPS negocio:** {float(lat):.6f}, {float(lon):.6f}")
        links = []
        if gmap:  links.append(f"[Google Maps]({gmap})")
        if gview: links.append(f"[Vista @18z]({gview})")
        if osm:   links.append(f"[OpenStreetMap]({osm})")
        if links:
            st.markdown(" · ".join(links))
    else:
        st.info("GPS no disponible aún.")

# === Etapa 2: Cliente y Negocio (detalle + comentario del asesor) ===
import streamlit as st

def _fmt_antiguedad(anios, meses):
    try:
        a = int(anios or 0); m = int(meses or 0)
        if a == 0 and m == 0:
            return ""
        return f"{a} año(s) y {m} mes(es)"
    except Exception:
        return ""

# Preferir lo guardado en reporte -> cliente_negocio
cn = (st.session_state.get("reporte", {}) or {}).get("cliente_negocio", {}) or {}
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
    neg_live.get("antiguedad_anios"), neg_live.get("antiguedad_meses")
) or "—"

# Comentario del asesor: preferir el de la valoración 3VAL; si no, obs_general
coment_asesor = (
    ((st.session_state.get("reporte", {}) or {}).get("valoracion_asesor", {}) or {}).get("comentario")
    or st.session_state.get("obs_general", "")
    or "—"
)

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

st.markdown("**Comentario del asesor**")
st.info(coment_asesor)


# =========================
# III. Valoración del asesor de crédito
# (insertar este bloque antes del "IV. Estado de Resultados")
# =========================

def _leer_valoracion_asesor():
    """Devuelve (dict_valoracion, fuente_str). Tolera faltantes."""
    # 1) Preferir lo guardado por Paso 3VAL en el reporte
    rep_val = st.session_state.get("reporte", {}).get("valoracion_asesor")
    if isinstance(rep_val, dict) and rep_val:
        return rep_val, "reporte.valoracion_asesor"
    # 2) Fallback: estado en vivo
    live_val = st.session_state.get("valoracion_asesor")
    if isinstance(live_val, dict) and live_val:
        return live_val, "session_state.valoracion_asesor"
    # 3) Nada
    return {}, "—"

val, val_src = _leer_valoracion_asesor()

# Campos con defaults seguros
conoc = int((val.get("conocimiento_0a10") or 0) if str(val.get("conocimiento_0a10") or "").strip() != "" else 0)
cred  = int((val.get("credibilidad_0a10") or 0) if str(val.get("credibilidad_0a10") or "").strip() != "" else 0)
dudas = (val.get("dudas_declaracion") or "Sin dudas")
clas  = (val.get("clasificacion") or "—")
fact  = float(val.get("factor_asesor_0a1") or 0.0)

ev_raw = val.get("evidencia", [])
if isinstance(ev_raw, str):
    evidencia = [s.strip() for s in ev_raw.split(",") if s.strip()]
elif isinstance(ev_raw, list):
    evidencia = [str(x).strip() for x in ev_raw if str(x).strip()]
else:
    evidencia = []
coment = (val.get("comentario") or "").strip()

# (Opcional) Detalle del cálculo del factor, si aplica
avg = (conoc + cred) / 2.0
base_calc = 0.6 + 0.04 * avg
mult_dudas_map = {"Sin dudas": 1.00, "Dudas leves": 0.85, "Dudas serias": 0.60}
mult_dudas = mult_dudas_map.get(dudas, 1.00)

st.subheader("III. Valoración del asesor de crédito")

colV1, colV2, colV3 = st.columns(3)
with colV1:
    st.metric("Conocimiento (0–10)", f"{conoc}")
with colV2:
    st.metric("Credibilidad (0–10)", f"{cred}")
with colV3:
    st.metric("Factor de confiabilidad", f"{fact:.2f}")

colV4, colV5 = st.columns(2)
with colV4:
    st.write(f"**Percepción de veracidad:** {dudas}")
with colV5:
    st.write(f"**Clasificación del caso:** {clas}")

# Evidencia observada
st.markdown("**Evidencia observada:**")
if evidencia:
    st.markdown("\n".join([f"- {e}" for e in evidencia]))
else:
    st.caption("—")

# Comentario del asesor
st.markdown("**Comentario del asesor:**")
st.info(coment or "—")

# Glosa del factor (si hay datos)
if (conoc or cred) and fact > 0:
    st.caption(
        f"Glosa del factor: base={base_calc:.2f} (0.60 + 0.04×promedio de conocimiento/credibilidad={avg:.1f}) × "
        f"ajuste por dudas={mult_dudas:.2f} → {base_calc * mult_dudas:.2f}"
        + (" (redondeado/limitado a [0.40–1.00])" if abs((base_calc * mult_dudas) - fact) > 1e-6 else "")
    )
# st.caption(f"Fuente de valoración: {val_src}")  # útil para depurar; dejar comentado si no quieres mostrarlo




# =========================
# III-b. Análisis de ventas
# (pegar después de la "Valoración del asesor" y antes del ER)
# =========================

def _num(x):
    try:
        if x is None: return 0.0
        return float(str(x).replace(",", ""))
    except Exception:
        return 0.0

def _fmt_col(x):
    try:
        return f"₡ {int(round(_num(x))):,}".replace(",", ".")
    except Exception:
        return "₡ 0"

def _ajuste_tipicidad(valor, tipicidad):
    """Regla simple como en 3A: Alto -10%, Bajo +10%, Típico sin ajuste."""
    if valor is None: 
        return None, "—"
    v = _num(valor)
    if tipicidad == "Alto":  return v * 0.90, "Alto → −10%"
    if tipicidad == "Bajo":  return v * 1.10, "Bajo → +10%"
    return v, "Típico (sin ajuste)"

def _desv_pct(a, b):
    """Desviación relativa promedio; None si no se puede."""
    a, b = _num(a), _num(b)
    if a <= 0 or b <= 0: 
        return None
    base = (a + b) / 2.0
    return abs(a - b) / base

def _precision_label(ape):
    """Clasifica precisión de la clienta según el APE (error porcentual absoluto)."""
    if ape is None: 
        return "Indefinida"
    if ape <= 0.20: 
        return "Alta (≤20%)"
    if ape <= 0.40: 
        return "Media (20–40%)"
    return "Baja (>40%)"

rep = st.session_state.get("reporte", {})

# 3A Top-down (declaración de la clienta)
vtd = rep.get("ventas_topdown", {}) or {}
top_raw      = vtd.get("monto_colones")
tipicidad    = vtd.get("tipicidad")
fuente       = vtd.get("fuente")
conf_cli     = vtd.get("confianza_cliente_0a10")
coment_td    = (vtd.get("comentario") or "").strip()
top_ajustado, txt_ajuste = _ajuste_tipicidad(top_raw, tipicidad) if top_raw else (None, "—")

# 3B Bottom-up
vbu = rep.get("ventas_bottomup", {}) or {}
bottom_val   = vbu.get("ventas_estimadas_colones")
coment_bu    = (vbu.get("comentario") or "").strip()

# 3C Insumos/Margen
vin = rep.get("ventas_insumos_simple", rep.get("ventas_insumos", {})) or {}
insumos_val  = None if vin.get("no_aplica") else vin.get("ventas_estimadas_colones")
coment_ins   = (vin.get("comentario") or "").strip()
tiene_regs   = vin.get("tiene_registros_compras", "")

# Conciliación (si existe)
vcon = rep.get("ventas_conciliacion", {}) or {}
ventas_conc  = vcon.get("ventas_conciliadas_colones")
max_dev      = vcon.get("desviacion_max_pct")   # ya viene como fracción (0–1) si usaste el código previo
pesos        = vcon.get("pesos", {})
det_conc     = vcon.get("detalle", {}) or {}

# Factor/confiabilidad del asesor (contexto)
val = rep.get("valoracion_asesor", {}) or {}
factor_asesor = val.get("factor_asesor_0a1")
dudas = val.get("dudas_declaracion")
coment_asesor = (val.get("comentario") or "").strip()

# Tabla de estimaciones
filas = [
    {"Ángulo": "Top-down (clienta)", "Monto bruto": _fmt_col(top_raw), "Ajuste": txt_ajuste if top_ajustado else "—", "Usado": _fmt_col(top_ajustado) if top_ajustado else "—"},
    {"Ángulo": "Bottom-up (operativa)", "Monto bruto": _fmt_col(bottom_val), "Ajuste": "—", "Usado": _fmt_col(bottom_val) if bottom_val else "—"},
    {"Ángulo": "Insumos/Margen", "Monto bruto": ("No aplica" if vin.get("no_aplica") else _fmt_col(insumos_val)), "Ajuste": "—", "Usado": "—" if vin.get("no_aplica") else (_fmt_col(insumos_val) if insumos_val else "—")},
]
st.subheader("III-b. Análisis de ventas")
st.caption("Comparativa de ángulos y precisión declarativa de la clienta.")

st.dataframe(
    pd.DataFrame(filas),
    use_container_width=True,
    hide_index=True
)

# Si hay conciliación, mostrar resultado y métricas de precisión
if ventas_conc:
    ventas_conc = _num(ventas_conc)
    # Error porcentual absoluto de la clienta (declaración ajustada vs conciliado)
    ape = None
    if top_ajustado and ventas_conc > 0:
        ape = abs(_num(top_ajustado) - ventas_conc) / ventas_conc
    # Desviación máxima entre métodos (si no viene precalculada, la calculamos)
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

    # Calidad de la fuente declarativa y confianza
    fuente_formal = fuente in ["Facturación electrónica", "POS/Datáfono", "Extractos bancarios/SINPE"]
    colQ1, colQ2, colQ3 = st.columns(3)
    with colQ1:
        st.write(f"**Fuente Top-down:** {fuente or '—'}")
        st.caption("Clasificación: " + ("Formal" if fuente_formal else ("—" if not fuente else "Informal")))
    with colQ2:
        st.write(f"**Confianza declarada por clienta:** {conf_cli if conf_cli is not None else '—'}/10")
    with colQ3:
        st.write(f"**Factor del asesor:** {f'{factor_asesor:.2f}' if factor_asesor else '—'}  ·  **Dudas:** {dudas or '—'}")

    # Pesos (si existen)
    if pesos:
        st.markdown("**Ponderaciones en conciliación (Top/Bottom/Insumos):** "
                    f"{pesos.get('top_down', 0):.2f} / {pesos.get('bottom_up', 0):.2f} / {pesos.get('insumos', 0):.2f}")

# Comentarios específicos
st.markdown("**Comentarios específicos de ventas:**")
comentarios = []
if coment_td:  comentarios.append(f"- Top-down (clienta): {coment_td}")
if coment_bu:  comentarios.append(f"- Bottom-up: {coment_bu}")
if coment_ins: comentarios.append(f"- Insumos/Margen: {coment_ins}")
if comentarios:
    st.markdown("\n".join(comentarios))
else:
    st.caption("—")

# Comentario del asesor (si no lo mostraste ya en la sección anterior y quieres reiterarlo aquí)
if coment_asesor:
    st.markdown("**Comentario del asesor:**")
    st.info(coment_asesor)

# Etiqueta cualitativa de precisión (si hay APE)
if ventas_conc and top_ajustado:
    etiqueta = _precision_label(ape)
    st.caption(f"**Etiqueta de precisión declarativa de la clienta:** {etiqueta}")


