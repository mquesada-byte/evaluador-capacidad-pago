# =========================
# PASO 1 – Datos del asesor (pantalla independiente)
# =========================
import datetime as dt
from zoneinfo import ZoneInfo
import time, requests
import streamlit as st
from streamlit_js_eval import get_geolocation

TZ = ZoneInfo("America/Costa_Rica")
USE_INTERNET_TIME = True
MAX_RERUNS = 6
SLEEP_SEC = 0.4

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

def swapped_links(lat, lon):
    lat_s, lon_s = f"{lat:.6f}", f"{lon:.6f}"
    return (
        f"https://www.google.com/maps/search/?api=1&query={lon_s},{lat_s}",
        f"https://www.openstreetmap.org/?mlat={lon_s}&mlon={lat_s}#map=18/{lon_s}/{lat_s}",
    )

def plausible_cr_area(lat, lon):
    return (8.0 <= lat <= 12.0) and (-90.0 <= lon <= -80.0)

def init_asesor_state():
    st.session_state.setdefault("step", 1)
    st.session_state.setdefault("asesor", {})
    st.session_state.setdefault("geo_request", False)
    st.session_state.setdefault("geo_status", "idle")
    st.session_state.setdefault("geo_attempts", 0)
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
        "gps": f"{a['lat']:.6f}, {a['lon']:.6f}" if a.get("lat") is not None and a.get("lon") is not None else "No disponible",
        "google_maps": a.get("maps_url"),
        "google_maps_vista": a.get("maps_url_alt"),
        "openstreetmap": a.get("osm_url"),
    }

if st.session_state.get("step", 1) == 1:
    init_asesor_state()
    asesor = st.session_state.asesor

    st.title("🧭 Paso 1: Datos del asesor")
    st.caption("La fecha y hora se registran automáticamente y no pueden ser modificadas.")

    asesor["nombre"] = st.text_input("Nombre completo del asesor *", value=asesor["nombre"])
    fecha_hora_registro = asesor["fecha_hora"].strftime("%d/%m/%Y %H:%M:%S")
    st.text_input("📅 Fecha y hora de registro",
                  value=fecha_hora_registro + (" (Internet)" if asesor.get("timestamp_source") == "internet" else " (Dispositivo)"),
                  disabled=True)

    st.write("**Ubicación GPS (opcional)**")
    col1, col2 = st.columns([0.45, 0.55])

    with col1:
        if st.button("📍 Obtener mi ubicación"):
            st.session_state.geo_request = True
            st.session_state.geo_status = "waiting"
            st.session_state.geo_attempts = 0
            asesor.update({"lat": None, "lon": None, "maps_url": None, "maps_url_alt": None, "osm_url": None})
            st.rerun()

        if st.session_state.geo_request and st.session_state.geo_status != "ok":
            loc = None
            try:
                loc = get_geolocation()
            except Exception:
                pass

            if isinstance(loc, dict):
                coords = loc.get("coords") or {}
                lat = coords.get("latitude"); lon = coords.get("longitude")
                msg = (loc.get("msg") or loc.get("message") or "").lower()

                if lat is not None and lon is not None and _coords_plausibles(lat, lon):
                    asesor["lat"], asesor["lon"] = float(lat), float(lon)
                    g, g_at, osm = maps_links(asesor["lat"], asesor["lon"])
                    asesor["maps_url"], asesor["maps_url_alt"], asesor["osm_url"] = g, g_at, osm
                    st.session_state.geo_status = "ok"; st.session_state.geo_request = False
                elif "denied" in msg:
                    st.session_state.geo_status = "denied"; st.session_state.geo_request = False
                elif "timeout" in msg:
                    st.session_state.geo_status = "timeout"; st.session_state.geo_request = False
                elif "unavailable" in msg:
                    st.session_state.geo_status = "unavailable"; st.session_state.geo_request = False
                else:
                    st.session_state.geo_attempts += 1
                    if st.session_state.geo_attempts < MAX_RERUNS:
                        with st.spinner("Solicitando permiso o esperando señal de GPS…"):
                            time.sleep(SLEEP_SEC)
                        st.rerun()
                    else:
                        st.session_state.geo_status = "error"; st.session_state.geo_request = False
            else:
                st.session_state.geo_attempts += 1
                if st.session_state.geo_attempts < MAX_RERUNS:
                    with st.spinner("Solicitando permiso o esperando señal de GPS…"):
                        time.sleep(SLEEP_SEC)
                    st.rerun()
                else:
                    st.session_state.geo_status = "error"; st.session_state.geo_request = False

    with col2:
        status = st.session_state.geo_status
        if asesor["lat"] is not None and asesor["lon"] is not None:
            lat, lon = asesor["lat"], asesor["lon"]
            st.success(f"Ubicación: {lat:.6f}, {lon:.6f}")
            st.markdown(f"[Abrir en Google Maps]({asesor['maps_url']}) · "
                        f"[Vista @18z]({asesor['maps_url_alt']}) · "
                        f"[OpenStreetMap]({asesor['osm_url']})")
            if not plausible_cr_area(lat, lon):
                g_sw, osm_sw = swapped_links(lat, lon)
                st.warning("Las coordenadas no parecen estar en Costa Rica. Prueba el orden invertido si el mapa no coincide:")
                st.markdown(f"• [Google (invertido)]({g_sw}) · [OSM (invertido)]({osm_sw})")
        else:
            msgs = {
                "waiting": "Solicitando permiso o esperando señal de GPS…",
                "denied": "Permiso de ubicación denegado en el navegador.",
                "timeout": "Tiempo de espera agotado al obtener la ubicación.",
                "unavailable": "Ubicación no disponible en este dispositivo/red.",
                "error": "No fue posible obtener la ubicación en este momento.",
                "idle": "Aún no hay coordenadas registradas.",
            }
            st.caption(msgs.get(status, "Aún no hay coordenadas registradas."))

    st.divider()

    disabled_next = not bool(asesor["nombre"].strip())
    colA, colB = st.columns([0.7, 0.3])
    with colA:
        st.write("Campo obligatorio: **Nombre del asesor**.")
    with colB:
        if st.button("Siguiente ➡️", key="next_step_1",
                     disabled=disabled_next, use_container_width=True):
            st.session_state.setdefault("reporte", {})
            st.session_state["reporte"]["asesor"] = asesor_para_reporte()
            st.session_state.step = 2
            st.rerun()

