# app.py – Paso 1: Datos del asesor (hora OK + GPS robusto + Fallback por IP)
import time
import datetime as dt
from zoneinfo import ZoneInfo
import requests
import streamlit as st
from streamlit_js_eval import get_geolocation

st.set_page_config(page_title="Evaluación Crédito - Paso 1", page_icon="🧭")

# =========================
# Configuración y utilidades
# =========================
TZ = ZoneInfo("America/Costa_Rica")
USE_INTERNET_TIME = True  # mantener hora exacta por Internet si está disponible

# Parámetros de geolocalización (reintentos controlados)
MAX_RERUNS = 6     # ~6 intentos
SLEEP_SEC = 0.4    # pausa breve entre intentos

def now_in_cr_via_internet():
    """Intenta obtener hora exacta por internet; si falla, retorna None."""
    try:
        r = requests.get("https://worldtimeapi.org/api/timezone/America/Costa_Rica", timeout=5)
        r.raise_for_status()
        j = r.json()
        return dt.datetime.fromisoformat(j["datetime"].replace("Z", "+00:00")).astimezone(TZ)
    except Exception:
        return None

def now_in_cr_fallback():
    return dt.datetime.now(TZ)

def _coords_plausibles(lat, lon):
    try:
        lat = float(lat); lon = float(lon)
        return -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0
    except Exception:
        return False

def geo_by_ip():
    """
    Aproxima ubicación por IP. Intenta varios proveedores públicos.
    Devuelve (lat, lon, fuente_texto) o (None, None, None) si falla.
    """
    endpoints = [
        ("https://ipapi.co/json/",           lambda j: (j.get("latitude"), j.get("longitude"), "ipapi.co")),
        ("https://ipwho.is/",                lambda j: (j.get("latitude"), j.get("longitude"), "ipwho.is")),
        ("https://ipinfo.io/json",           # ipinfo devuelve "loc": "lat,lon"
         lambda j: (j.get("loc").split(",")[0] if j.get("loc") else None,
                    j.get("loc").split(",")[1] if j.get("loc") else None,
                    "ipinfo.io")),
    ]
    for url, parser in endpoints:
        try:
            r = requests.get(url, timeout=5)
            if r.ok:
                j = r.json()
                lat, lon, src = parser(j)
                if lat is not None and lon is not None and _coords_plausibles(lat, lon):
                    return float(lat), float(lon), src
        except Exception:
            continue
    return None, None, None

# ==========
# Estado
# ==========
def init_asesor_state():
    st.session_state.setdefault("step", 1)
    st.session_state.setdefault("asesor", {})
    st.session_state.setdefault("geo_request", False)   # solicitar geolocalización (GPS)
    st.session_state.setdefault("geo_status", "idle")   # idle|waiting|ok|denied|timeout|unavailable|error
    st.session_state.setdefault("geo_attempts", 0)      # contador de intentos

    asesor = st.session_state.asesor
    asesor.setdefault("nombre", "")

    # === HORA: NO TOCAR (queda como te gustó) ===
    if "fecha_hora" not in asesor:
        ts = None
        if USE_INTERNET_TIME:
            ts = now_in_cr_via_internet()
            asesor["timestamp_source"] = "internet" if ts else "device"
        if ts is None:
            ts = now_in_cr_fallback()
            asesor["timestamp_source"] = "device"
        asesor["fecha_hora"] = ts  # se fija 1 vez e inmutable para el usuario
    # ============================================

    asesor.setdefault("lat", None)
    asesor.setdefault("lon", None)
    asesor.setdefault("maps_url", None)
    asesor.setdefault("ubicacion_metodo", None)   # "gps" | "ip"
    asesor.setdefault("ubicacion_fuente", None)   # proveedor IP (si aplica)

init_asesor_state()
asesor = st.session_state.asesor

# ==========
# Interfaz UI
# ==========
st.title("🧭 Paso 1: Datos del asesor")
st.caption("Complete la información. La fecha y hora se registran automáticamente y no pueden ser modificadas.")

# Nombre (obligatorio)
asesor["nombre"] = st.text_input(
    "Nombre completo del asesor *",
    value=asesor["nombre"],
    placeholder="Ej.: María Pérez Delgado",
)

# Fecha y hora (solo lectura) — indicador de fuente
fecha_hora_registro = asesor["fecha_hora"].strftime("%d/%m/%Y %H:%M:%S")
st.text_input(
    "📅 Fecha y hora de registro",
    value=fecha_hora_registro + (" (Internet)" if asesor.get("timestamp_source") == "internet" else " (Dispositivo)"),
    disabled=True
)

# ===========================
# Ubicación – GPS + Fallback IP
# ===========================
st.write("**Ubicación (GPS o IP aproximada)**")
col1, col2 = st.columns([0.52, 0.48])

with col1:
    c1, c2 = st.columns(2)
    with c1:
        if st.button("📍 Obtener por GPS"):
            st.session_state.geo_request = True
            st.session_state.geo_status = "waiting"
            st.session_state.geo_attempts = 0
            asesor["lat"] = None
            asesor["lon"] = None
            asesor["maps_url"] = None
            asesor["ubicacion_metodo"] = None
            asesor["ubicacion_fuente"] = None
            st.rerun()
    with c2:
        if st.button("🌐 Usar ubicación por IP"):
            # Llamada síncrona desde el servidor (aproximado)
            lat, lon, src = geo_by_ip()
            if lat is not None and lon is not None:
                asesor["lat"] = lat
                asesor["lon"] = lon
                asesor["maps_url"] = f"https://www.google.com/maps?q={lat},{lon}"
                asesor["ubicacion_metodo"] = "ip"
                asesor["ubicacion_fuente"] = src
                st.session_state.geo_request = False
                st.session_state.geo_status = "ok"
                st.success("Ubicación aproximada por IP establecida.")
            else:
                st.session_state.geo_request = False
                st.session_state.geo_status = "error"
                st.warning("No fue posible obtener ubicación por IP en este momento. Intenta de nuevo o usa GPS.")

    # Ejecución GPS fuera del botón (captura en reruns)
    if st.session_state.geo_request and st.session_state.geo_status != "ok":
        try:
            loc = get_geolocation()  # sin params por compatibilidad
        except Exception:
            loc = None

        if isinstance(loc, dict):
            coords = loc.get("coords") or {}
            lat, lon = coords.get("latitude"), coords.get("longitude")
            msg = (loc.get("msg") or loc.get("message") or "").lower()

            if lat is not None and lon is not None and _coords_plausibles(lat, lon):
                asesor["lat"] = float(lat)
                asesor["lon"] = float(lon)
                asesor["maps_url"] = f"https://www.google.com/maps?q={asesor['lat']},{asesor['lon']}"
                asesor["ubicacion_metodo"] = "gps"
                asesor["ubicacion_fuente"] = "navigator.geolocation"
                st.session_state.geo_status = "ok"
                st.session_state.geo_request = False
            elif "denied" in msg:
                st.session_state.geo_status = "denied"
                st.session_state.geo_request = False
            elif "timeout" in msg:
                st.session_state.geo_status = "timeout"
                st.session_state.geo_request = False
            elif "unavailable" in msg:
                st.session_state.geo_status = "unavailable"
                st.session_state.geo_request = False
            else:
                st.session_state.geo_attempts += 1
                if st.session_state.geo_attempts < MAX_RERUNS:
                    with st.spinner("Solicitando permiso o esperando señal de GPS…"):
                        time.sleep(SLEEP_SEC)
                    st.rerun()
                else:
                    st.session_state.geo_status = "error"
                    st.session_state.geo_request = False
        else:
            st.session_state.geo_attempts += 1
            if st.session_state.geo_attempts < MAX_RERUNS:
                with st.spinner("Solicitando permiso o esperando señal de GPS…"):
                    time.sleep(SLEEP_SEC)
                st.rerun()
            else:
                st.session_state.geo_status = "error"
                st.session_state.geo_request = False

with col2:
    status = st.session_state.geo_status
    if asesor["lat"] is not None and asesor["lon"] is not None:
        metodo = "GPS" if asesor.get("ubicacion_metodo") == "gps" else "IP aproximada"
        fuente = asesor.get("ubicacion_fuente") or ""
        st.success(f"Ubicación ({metodo}): {asesor['lat']:.6f}, {asesor['lon']:.6f}")
        st.markdown(f"[Abrir en Google Maps]({asesor['maps_url']})")
        if asesor.get("ubicacion_metodo") == "ip":
            st.caption(f"Fuente IP: {fuente}. Precisión limitada (ciudad/área).")
    else:
        if status == "waiting":
            st.info("Solicitando permiso o esperando señal de GPS…")
        elif status == "denied":
            st.warning("Permiso de ubicación denegado en el navegador.")
        elif status == "timeout":
            st.warning("Tiempo de espera agotado al obtener la ubicación.")
        elif status == "unavailable":
            st.warning("Ubicación no disponible en este dispositivo/red.")
        elif status == "error":
            st.warning("No fue posible obtener la ubicación. Prueba con el botón de IP o vuelve a intentar GPS.")
        else:
            st.caption("Aún no hay coordenadas registradas.")

st.divider()

# ===========================
# Validación y navegación
# ===========================
disabled_next = not bool(asesor["nombre"].strip())
colA, colB = st.columns([0.7, 0.3])
with colA:
    st.write("Campo obligatorio: **Nombre del asesor**.")
with colB:
    if st.button("Siguiente ➡️", disabled=disabled_next, use_container_width=True):
        st.session_state.step = 2
        st.success("Datos del asesor guardados. Avanzando al Paso 2…")



