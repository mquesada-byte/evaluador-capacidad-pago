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
        a = int(anios or 0); m = int(meses or 0)
        if a == 0 and m == 0:
            return ""
        return f"{a} año(s) y {m} mes(es)"
    except Exception:
        return ""

def _num(x):
    try:
        if x is None: return 0.0
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
    if tipicidad == "Alto":  return v * 0.90, "Alto → −10%"
    if tipicidad == "Bajo":  return v * 1.10, "Bajo → +10%"
    return v, "Típico (sin ajuste)"

def _desv_pct(a, b):
    a, b = _num(a), _num(b)
    if a <= 0 or b <= 0:
        return None
    base = (a + b) / 2.0
    return abs(a - b) / base

def _precision_label(ape):
    if ape is None: return "Indefinida"
    if ape <= 0.20: return "Alta (≤20%)"
    if ape <= 0.40: return "Media (20–40%)"
    return "Baja (>40%)"

# ---------- Lectura de datos desde session_state ----------
ases = st.session_state.get("asesor", {}) or {}
rep   = st.session_state.get("reporte", {}) or {}
rep_ases = rep.get("asesor", {}) or {}

# Asesor
asesor_nombre = rep_ases.get("nombre") or ases.get("nombre") or "(sin registrar)"
fecha_str = rep_ases.get("fecha_hora") or _fmt_dt(ases.get("fecha_hora")) or dt.datetime.now(TZ).strftime("%d/%m/%Y %H:%M:%S")
fuente_hora = rep_ases.get("hora_fuente") or ("Internet" if ases.get("timestamp_source") == "internet"
                                             else ("Dispositivo" if ases.get("timestamp_source") else "—"))

# GPS
lat = ases.get("lat"); lon = ases.get("lon")
if lat is None or lon is None:
    lat, lon = _parse_gps_str(rep_ases.get("gps"))
gmap = rep_ases.get("google_maps"); gview = rep_ases.get("google_maps_vista"); osm = rep_ases.get("openstreetmap")
if (not gmap or not osm) and (lat is not None and lon is not None):
    gmap_gen, gview_gen, osm_gen = _maps_links(float(lat), float(lon))
    gmap = gmap or gmap_gen
    gview = gview or gview_gen
    osm   = osm or osm_gen

# Cliente / negocio
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
antiguedad = cn.get("antiguedad") or _fmt_antiguedad(neg_live.get("antiguedad_anios"), neg_live.get("antiguedad_meses")) or "—"

# Valoración asesor
val = rep.get("valoracion_asesor", {}) or st.session_state.get("valoracion_asesor", {}) or {}
conoc = int((val.get("conocimiento_0a10") or 0) if str(val.get("conocimiento_0a10") or "").strip() != "" else 0)
cred  = int((val.get("credibilidad_0a10") or 0) if str(val.get("credibilidad_0a10") or "").strip() != "" else 0)
dudas = (val.get("dudas_declaracion") or "Sin dudas")
clas  = (val.get("clasificacion") or "—")
factor_asesor = float(val.get("factor_asesor_0a1") or 0.0)
ev_raw = val.get("evidencia", [])
if isinstance(ev_raw, str):
    evidencia = [s.strip() for s in ev_raw.split(",") if s.strip()]
elif isinstance(ev_raw, list):
    evidencia = [str(x).strip() for x in ev_raw if str(x).strip()]
else:
    evidencia = []
coment_val = (val.get("comentario") or "").strip()

# Ventas
vtd = rep.get("ventas_topdown", {}) or {}
top_raw      = vtd.get("monto_colones")
tipicidad    = vtd.get("tipicidad")
fuente_td    = vtd.get("fuente")
conf_cli     = vtd.get("confianza_cliente_0a10")   # ✅ Ajuste aquí
coment_td    = (vtd.get("comentario") or "").strip()
top_ajustado, txt_ajuste = _ajuste_tipicidad(top_raw, tipicidad) if top_raw else (None, "—")

vbu = rep.get("ventas_bottomup", {}) or {}
bottom_val   = vbu.get("ventas_estimadas_colones")
coment_bu    = (vbu.get("comentario") or "").strip()

vin = rep.get("ventas_insumos_simple", rep.get("ventas_insumos", rep.get("ventas_p5", {}))) or {}  # ✅ Ajuste aquí
insumos_val  = None if vin.get("no_aplica") else vin.get("ventas_estimadas_colones")
coment_ins   = (vin.get("comentario") or "").strip()

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
