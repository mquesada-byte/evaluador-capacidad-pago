# =========================
# PASO 1 – Datos del asesor (pantalla independiente)
# =========================
import datetime as dt
from zoneinfo import ZoneInfo
import requests
import streamlit as st
from streamlit_js_eval import get_geolocation

st.set_page_config(page_title="Paso 1: Datos del asesor", page_icon="🧭")

TZ = ZoneInfo("America/Costa_Rica")
USE_INTERNET_TIME = True

# ---- Helpers de tiempo ----
def now_in_cr_via_internet():
    try:
        r = requests.get("https://worldtimeapi.org/api/timezone/America/Costa_Rica", timeout=5)
        r.raise_for_status()
        j = r.json()
        return dt.datetime.fromisoformat(j["datetime"].replace("Z", "+00:00")).astimezone(TZ)
    except Exception:
        return None

def now_in_cr_fallback():
    return dt.datetime.now(TZ)

# ---- Helpers de GPS / mapas ----
def _coords_plausibles(lat, lon):
    try:
        lat = float(lat); lon = float(lon)
        return -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0
    except Exception:
        return False

def maps_links(lat, lon):
    lat_s, lon_s = f"{lat:.6f}", f"{lon:.6f}"
    google = f"https://www.google.com/maps/search/?api=1&query={lat_s},{lon_s}"
    google_at = f"https://www.google.com/maps/@{lat_s},{lon_s},18z"
    osm = f"https://www.openstreetmap.org/?mlat={lat_s}&mlon={lon_s}#map=18/{lat_s}/{lon_s}"
    return google, google_at, osm

def plausible_cr_area(lat, lon):
    return (8.0 <= lat <= 12.0) and (-90.0 <= lon <= -80.0)

# ---- Estado inicial ----
def init_asesor_state():
    st.session_state.setdefault("asesor", {})
    st.session_state.setdefault("geo_request", False)
    st.session_state.setdefault("geo_status", "idle")

    a = st.session_state.asesor
    a.setdefault("nombre", "")
    if "fecha_hora" not in a:
        ts = now_in_cr_via_internet() if USE_INTERNET_TIME else None
        a["timestamp_source"] = "internet" if ts else "device"
        a["fecha_hora"] = ts or now_in_cr_fallback()
    a.setdefault("lat", None); a.setdefault("lon", None)
    a.setdefault("maps_url", None); a.setdefault("maps_url_alt", None); a.setdefault("osm_url", None)

def asesor_para_reporte():
    a = st.session_state.get("asesor", {})
    fecha = a.get("fecha_hora")
    return {
        "nombre": (a.get("nombre") or "").strip(),
        "fecha_hora": fecha.strftime("%d/%m/%Y %H:%M:%S") if fecha else "N/D",
        "hora_fuente": "Internet" if a.get("timestamp_source") == "internet" else "Dispositivo",
        "gps": f"{a['lat']:.6f}, {a['lon']:.6f}"
               if a.get("lat") is not None and a.get("lon") is not None
               else "No disponible",
        "google_maps": a.get("maps_url"),
        "google_maps_vista": a.get("maps_url_alt"),
        "openstreetmap": a.get("osm_url"),
    }

# =================== UI ===================
init_asesor_state()
asesor = st.session_state.asesor

st.title("🧭 Paso 1: Datos del asesor")
st.caption("La fecha y hora se registran automáticamente y no pueden ser modificadas.")

# Nombre con placeholder
asesor["nombre"] = st.text_input(
    "Nombre completo del asesor *",
    value=asesor["nombre"],
    placeholder="Ej.: Steven Gerardo Salas Solano",
    help="Escribe tu nombre y apellidos completos."
)

# Fecha/hora (solo lectura)
fecha_hora_registro = asesor["fecha_hora"].strftime("%d/%m/%Y %H:%M:%S")
st.text_input(
    "📅 Fecha y hora de registro",
    value=fecha_hora_registro + (" (Internet)" if asesor.get("timestamp_source") == "internet" else " (Dispositivo)"),
    disabled=True
)

st.write("**Ubicación GPS (opcional)**")
col1, col2 = st.columns([0.45, 0.55])

with col1:
    if st.button("📍 Obtener mi ubicación"):
        st.session_state.geo_request = True
        st.session_state.geo_status = "waiting"
        asesor.update({"lat": None, "lon": None, "maps_url": None, "maps_url_alt": None, "osm_url": None})

# Si hay una solicitud activa → pedir geolocalización
if st.session_state.geo_request and st.session_state.geo_status != "ok":
    loc = get_geolocation()
    if isinstance(loc, dict) and "coords" in loc and loc["coords"].get("latitude") is not None:
        coords = loc["coords"]
        lat, lon = coords.get("latitude"), coords.get("longitude")
        if _coords_plausibles(lat, lon):
            asesor["lat"], asesor["lon"] = float(lat), float(lon)
            g, g_at, osm = maps_links(asesor["lat"], asesor["lon"])
            asesor["maps_url"], asesor["maps_url_alt"], asesor["osm_url"] = g, g_at, osm
            st.session_state.geo_status = "ok"
            st.session_state.geo_request = False
    else:
        st.session_state.geo_status = "waiting"
        st.caption("Esperando autorización del navegador… por favor permite el acceso a la ubicación.")

with col2:
    status = st.session_state.geo_status
    if asesor["lat"] is not None and asesor["lon"] is not None:
        lat, lon = asesor["lat"], asesor["lon"]
        st.success(f"Ubicación: {lat:.6f}, {lon:.6f}")
        st.markdown(f"[Abrir en Google Maps]({asesor['maps_url']}) · "
                    f"[Vista @18z]({asesor['maps_url_alt']}) · "
                    f"[OpenStreetMap]({asesor['osm_url']})")
        if not plausible_cr_area(lat, lon):
            st.warning("Las coordenadas no parecen estar en Costa Rica.")
    else:
        msgs = {
            "waiting": "Solicitando permiso o esperando señal de GPS…",
            "denied": "Permiso de ubicación denegado en el navegador.",
            "unavailable": "Ubicación no disponible en este dispositivo/red.",
            "error": "No fue posible obtener la ubicación en este momento.",
            "idle": "Aún no hay coordenadas registradas.",
        }
        st.caption(msgs.get(status, "Aún no hay coordenadas registradas."))

st.divider()

# ---- Navegación (multipágina) ----
disabled_next = not bool(asesor["nombre"].strip())
colA, colB = st.columns([0.7, 0.3])
with colA:
    st.write("Campo obligatorio: **Nombre del asesor**.")
with colB:
    if st.button("Siguiente ➡️", key="next_step_1", disabled=disabled_next, use_container_width=True):
        st.session_state.setdefault("reporte", {})
        st.session_state["reporte"]["asesor"] = asesor_para_reporte()
        st.session_state["done_01"] = True
        # Navegar al Paso 2
        try:
            st.switch_page("pages/02_Cliente_y_negocio.py")
        except Exception:
            st.success("Datos guardados. Continúa con el siguiente paso:")
            st.page_link("pages/02_Cliente_y_negocio.py", label="➡️ Ir a Paso 2 – Cliente y negocio")
            st.stop()



