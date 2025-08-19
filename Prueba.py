# app.py – Paso 1: Datos del asesor (hora OK + geolocalización robusta y compatible + links de mapa estables)
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
USE_INTERNET_TIME = True  # dejar hora exacta por Internet si está disponible

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

# ---- Helpers para links de mapas (clave para evitar desvíos) ----
def maps_links(lat: float, lon: float):
    """Devuelve links estables a Google y OSM en orden lat,lon."""
    lat_s = f"{lat:.6f}"
    lon_s = f"{lon:.6f}"
    google = f"https://www.google.com/maps/search/?api=1&query={lat_s},{lon_s}"
    google_at = f"https://www.google.com/maps/@{lat_s},{lon_s},18z"
    osm = f"https://www.openstreetmap.org/?mlat={lat_s}&mlon={lon_s}#map=18/{lat_s}/{lon_s}"
    return google, google_at, osm

def swapped_links(lat: float, lon: float):
    """Links con orden invertido (lon,lat) por si el proveedor interpreta al revés."""
    lat_s = f"{lat:.6f}"
    lon_s = f"{lon:.6f}"
    google_sw = f"https://www.google.com/maps/search/?api=1&query={lon_s},{lat_s}"
    osm_sw = f"https://www.openstreetmap.org/?mlat={lon_s}&mlon={lat_s}#map=18/{lon_s}/{lat_s}"
    return google_sw, osm_sw

def plausible_cr_area(lat: float, lon: float) -> bool:
    """Chequeo rápido para Costa Rica (8–12 lat, -90–-80 lon aprox)."""
    return (8.0 <= lat <= 12.0) and (-90.0 <= lon <= -80.0)

# ==========
# Estado
# ==========
def init_asesor_state():
    st.session_state.setdefault("step", 1)
    st.session_state.setdefault("asesor", {})
    st.session_state.setdefault("geo_request", False)   # solicitar geolocalización
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
    asesor.setdefault("maps_url_alt", None)
    asesor.setdefault("osm_url", None)

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
# Ubicación GPS (opcional) – ROBUSTA y COMPATIBLE
# ===========================
st.write("**Ubicación GPS (opcional)**")
col1, col2 = st.columns([0.45, 0.55])

with col1:
    if st.button("📍 Obtener mi ubicación"):
        st.session_state.geo_request = True
        st.session_state.geo_status = "waiting"
        st.session_state.geo_attempts = 0
        asesor["lat"] = None
        asesor["lon"] = None
        asesor["maps_url"] = None
        asesor["maps_url_alt"] = None
        asesor["osm_url"] = None
        st.rerun()

    # Ejecutar fuera del botón para capturar el resultado en reruns
    if st.session_state.geo_request and st.session_state.geo_status != "ok":
        try:
            # Llamada sin parámetros (compatibilidad con tu versión de streamlit_js_eval)
            loc = get_geolocation()
        except Exception:
            loc = None  # si la lib falla, seguimos con reintentos amables

        if isinstance(loc, dict):
            # Distintas formas posibles de la respuesta según versión
            coords = loc.get("coords") or {}
            lat = coords.get("latitude")
            lon = coords.get("longitude")

            # Algunas variantes ponen errores en 'msg'/'message'
            msg = (loc.get("msg") or loc.get("message") or "").lower()

            # Éxito con coordenadas plausibles
            if lat is not None and lon is not None and _coords_plausibles(lat, lon):
                asesor["lat"] = float(lat)
                asesor["lon"] = float(lon)
                g, g_at, osm = maps_links(asesor["lat"], asesor["lon"])
                asesor["maps_url"] = g
                asesor["maps_url_alt"] = g_at
                asesor["osm_url"] = osm
                st.session_state.geo_status = "ok"
                st.session_state.geo_request = False

            # Errores explícitos
            elif "denied" in msg:
                st.session_state.geo_status = "denied"
                st.session_state.geo_request = False
            elif "timeout" in msg:
                st.session_state.geo_status = "timeout"
                st.session_state.geo_request = False
            elif "unavailable" in msg:
                st.session_state.geo_status = "unavailable"
                st.session_state.geo_request = False

            # Sin coords ni error claro: reintenta con espera corta
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
            # Primeros renders suelen devolver None: reintenta antes de declarar error
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
        lat, lon = asesor["lat"], asesor["lon"]
        st.success(f"Ubicación: {lat:.6f}, {lon:.6f}")

        # Enlaces confiables
        st.markdown(
            f"[Abrir en Google Maps]({asesor['maps_url']}) · "
            f"[Vista @18z]({asesor['maps_url_alt']}) · "
            f"[OpenStreetMap]({asesor['osm_url']})"
        )

        # Si parece fuera de Costa Rica, ofrece enlaces “invertidos”
        if not plausible_cr_area(lat, lon):
            g_sw, osm_sw = swapped_links(lat, lon)
            st.warning(
                "Las coordenadas no parecen estar en Costa Rica. "
                "Si el mapa abre en un lugar extraño, prueba el orden invertido:"
            )
            st.markdown(f"• [Google (invertido)]({g_sw}) · [OSM (invertido)]({osm_sw})")
    else:
        if status == "waiting":
            st.info("Solicitando permiso o esperando señal de GPS…")
        elif status == "denied":
            st.warning("Permiso de ubicación denegado en el navegador. Actívalo en el candado de la URL y vuelve a intentar.")
        elif status == "timeout":
            st.warning("Tiempo de espera agotado al obtener la ubicación.")
        elif status == "unavailable":
            st.warning("Ubicación no disponible en este dispositivo/red.")
        elif status == "error":
            st.warning("No fue posible obtener la ubicación en este momento. Puedes reintentar.")
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



