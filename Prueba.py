# app.py
import datetime as dt
import streamlit as st

# Componente para leer geolocalización del navegador
from streamlit_js_eval import get_geolocation

st.set_page_config(page_title="Evaluación Crédito - Paso 1", page_icon="🧭")

# ---------- Estado global ----------
if "step" not in st.session_state:
    st.session_state.step = 1

if "asesor" not in st.session_state:
    st.session_state.asesor = {
        "nombre": "",
        "fecha": dt.date.today(),  # se setea automático
        "lat": None,
        "lon": None,
        "maps_url": None,
    }

# ---------- UI: Paso 1 - Datos del asesor ----------
st.title("🧭 Paso 1: Datos del asesor")

st.caption("Complete la información. La fecha se carga automáticamente y la ubicación GPS es opcional (requiere permiso del navegador).")

# Nombre completo (obligatorio)
st.session_state.asesor["nombre"] = st.text_input(
    "Nombre completo del asesor *",
    value=st.session_state.asesor["nombre"],
    placeholder="Ej.: María Pérez Delgado",
)

# Fecha automática (editable por si necesitás corregir)
st.session_state.asesor["fecha"] = st.date_input(
    "Fecha de registro",
    value=st.session_state.asesor["fecha"],
    format="DD/MM/YYYY",
)

# Obtener GPS del navegador
st.write("**Ubicación GPS (opcional)**")
col1, col2 = st.columns([0.45, 0.55])
with col1:
    if st.button("📍 Obtener mi ubicación"):
        loc = get_geolocation()  # abrirá el prompt de permiso en el navegador
        # get_geolocation devuelve un dict con latitud/longitud/accuracy si el usuario acepta
        if loc and "coords" in loc and loc["coords"].get("latitude") is not None:
            lat = float(loc["coords"]["latitude"])
            lon = float(loc["coords"]["longitude"])
            st.session_state.asesor["lat"] = lat
            st.session_state.asesor["lon"] = lon
            st.session_state.asesor["maps_url"] = f"https://www.google.com/maps?q={lat},{lon}"
        else:
            st.info("No se pudo obtener la ubicación (permiso denegado o no disponible).")
with col2:
    if st.session_state.asesor["lat"] and st.session_state.asesor["lon"]:
        st.success(
            f"Ubicación guardada: {st.session_state.asesor['lat']:.6f}, "
            f"{st.session_state.asesor['lon']:.6f}"
        )
        st.markdown(
            f"[Abrir en Google Maps]({st.session_state.asesor['maps_url']})"
        )
    else:
        st.caption("Aún no hay coordenadas registradas.")

st.divider()

# Validación mínima y navegación
disabled_next = not bool(st.session_state.asesor["nombre"].strip())

colA, colB = st.columns([0.7, 0.3])
with colA:
    st.write("Campos obligatorios: **Nombre**.")
with colB:
    if st.button("Siguiente ➡️", disabled=disabled_next, use_container_width=True):
        st.session_state.step = 2
        st.success("Datos del asesor guardados. Avanzando al Paso 2…")

# Debug opcional (ocúltalo en producción)
# st.json(st.session_state.asesor)

