# app.py – Paso 1: Datos del asesor (robusto con hora por Internet y mejor manejo de geolocalización)
import datetime as dt
from zoneinfo import ZoneInfo
import requests
import streamlit as st
from streamlit_js_eval import get_geolocation

st.set_page_config(page_title="Evaluación Crédito - Paso 1", page_icon="🧭")

TZ = ZoneInfo("America/Costa_Rica")
USE_INTERNET_TIME = True
GEO_MAX_ATTEMPTS = 3  # reintentos suaves para evitar "no se pudo" prematuro

# ---------- Utilidades ----------
def now_in_cr_via_internet():
    """Intenta obtener hora exacta por internet; si falla, retorna None."""
    try:
        # Servicio público simple
        r = requests.get("https://worldtimeapi.org/api/timezone/America/Costa_Rica", timeout=5)
        r.raise_for_status()
        j = r.json()
        # 'datetime' viene en ISO con tz; convertimos a datetime aware
        return dt.datetime.fromisoformat(j["datetime"].replace("Z", "+00:00")).astimezone(TZ)
    except Exception:
        return None

def now_in_cr_fallback():
    return dt.datetime.now(TZ)

# ---------- Estado ----------
def init_asesor_state():
    st.session_state.setdefault("step", 1)
    st.session_state.setdefault("asesor", {})
    st.session_state.setdefault("geo_request", False)     # solicitar geolocalización
    st.session_state.setdefault("geo_status", "idle")     # idle|waiting|ok|denied|unavailable|timeout|error
    st.session_state.setdefault("geo_attempts", 0)        # contador de intentos

    asesor = st.session_state.asesor
    asesor.setdefault("nombre", "")
    if "fecha_hora" not in asesor:
        # Intento por Internet primero
        ts = None
        if USE_INTERNET_TIME:
            ts = now_in_cr_via_internet()
            asesor["timestamp_source"] = "internet" if ts else "device"
        if ts is None:
            ts = now_in_cr_fallback()
            asesor["timestamp_source"] = "device"
        asesor["fecha_hora"] = ts  # se fija 1 vez

    asesor.setdefault("lat", None)
    asesor.setdefault("lon", None)
    asesor.setdefault("maps_url", None)

init_asesor_state()
asesor = st.session_state.asesor

# ---------- UI ----------
st.title("🧭 Paso 1: Datos del asesor")
st.caption("Complete la información. La fecha y hora se registran automáticamente y no pueden ser modificadas.")

# Nombre (obligatorio)
asesor["nombre"] = st.text_input(
    "Nombre completo del asesor *",
    value=asesor["nombre"],
    placeholder="Ej.: María Pérez Delgado",
)

# Fecha y hora (solo lectura)
fecha_hora_registro = asesor["fecha_hora"].strftime("%d/%m/%Y %H:%M:%S")
st.text_input(
    "📅 Fecha y hora de registro",
    value=fecha_hora_registro + (" (Internet)" if asesor.get("timestamp_source") == "internet" else " (Dispositivo)"),
    disabled=True
)

# Ubicación GPS (opcional)
st.write("**Ubicación GPS (opcional)**")
col1, col2 = st.columns([0.45, 0.55])

with col1:
    if st.button("📍 Obtener mi ubicación"):
        # Preparar solicitud y limpiar estado anterior
        st.session_state.geo_request = True
        st.session_state.geo_status = "waiting"
        st.session_state.geo_attempts = 0
        asesor["lat"] = None
        asesor["lon"] = None
        asesor["maps_url"] = None

    # Ejecutar la solicitud fuera del botón
    if st.session_state.geo_request and st.session_state.geo_status != "ok":
        loc = get_geolocation()
        # Algunos navegadores devuelven None en el primer ciclo: esperamos sin error
        if loc and isinstance(loc, dict):
            # Casos de éxito
            coords = loc.get("coords") or {}
            lat = coords.get("latitude")
            lon = coords.get("longitude")

            # Algunas implementaciones retornan un mensaje de error textual
            msg = (loc.get("msg") or loc.get("message") or "").lower()
            if lat is not None and lon is not None:
                asesor["lat"] = float(lat)
                asesor["lon"] = float(lon)
                asesor["maps_url"] = f"https://www.google.com/maps?q={asesor['lat']},{asesor['lon']}"
                st.session_state.geo_status = "ok"
                st.session_state.geo_request = False
            elif "denied" in msg or "permission" in msg and "denied" in msg:
                st.session_state.geo_status = "denied"
                st.session_state.geo_request = False
            elif "timeout" in msg:
                st.session_state.geo_status = "timeout"
                st.session_state.geo_request = False
            elif "unavailable" in msg:
                st.session_state.geo_status = "unavailable"
                st.session_state.geo_request = False
            else:
                # Aún sin coords ni error claro: sumamos intento y esperamos
                st.session_state.geo_attempts += 1
                if st.session_state.geo_attempts >= GEO_MAX_ATTEMPTS:
                    st.session_state.geo_status = "error"  # genérico
                    st.session_state.geo_request = False
                else:
                    st.info("Solicitando permiso o esperando la ubicación…")
        else:
            # Primer ciclo típico (None): mostramos mensaje amable sin error
            st.session_state.geo_attempts += 1
            if st.session_state.geo_attempts < GEO_MAX_ATTEMPTS:
                st.info("Solicitando permiso o esperando la ubicación…")
            else:
                st.session_state.geo_status = "error"
                st.session_state.geo_request = False

# Mensajería de estado clara (nada de “no se pudo” anticipado)
status = st.session_state.geo_status
with col2:
    if asesor["lat"] is not None and asesor["lon"] is not None:
        st.success(f"Ubicación: {asesor['lat']:.6f}, {asesor['lon']:.6f}")
        st.markdown(f"[Abrir en Google Maps]({asesor['maps_url']})")
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
            st.warning("No fue posible obtener la ubicación en este momento. Puedes reintentar.")
        else:
            st.caption("Aún no hay coordenadas registradas.")

st.divider()

# Validación y navegación
disabled_next = not bool(asesor["nombre"].strip())
colA, colB = st.columns([0.7, 0.3])
with colA:
    st.write("Campo obligatorio: **Nombre del asesor**.")
with colB:
    if st.button("Siguiente ➡️", disabled=disabled_next, use_container_width=True):
        st.session_state.step = 2
        st.success("Datos del asesor guardados. Avanzando al Paso 2…")


