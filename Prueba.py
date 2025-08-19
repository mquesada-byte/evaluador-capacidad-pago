# app.py – Paso 1: Datos del asesor
import datetime as dt
import streamlit as st
from streamlit_js_eval import get_geolocation

st.set_page_config(page_title="Evaluación Crédito - Paso 1", page_icon="🧭")

# ---------- Inicialización robusta del estado ----------
def init_asesor_state():
    st.session_state.setdefault("step", 1)
    st.session_state.setdefault("asesor", {})
    st.session_state.setdefault("geo_request", False)   # <-- NUEVO flag
    asesor = st.session_state.asesor
    asesor.setdefault("nombre", "")
    asesor.setdefault("fecha_hora", dt.datetime.now())  # se setea una sola vez
    asesor.setdefault("lat", None)
    asesor.setdefault("lon", None)
    asesor.setdefault("maps_url", None)
init_asesor_state()
asesor = st.session_state.asesor

# ---------- UI: Paso 1 ----------
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
st.text_input("📅 Fecha y hora de registro", value=fecha_hora_registro, disabled=True)

# Ubicación GPS (opcional)
st.write("**Ubicación GPS (opcional)**")
col1, col2 = st.columns([0.45, 0.55])
with col1:
    # Botón que activa la solicitud de geolocalización
    if st.button("📍 Obtener mi ubicación"):
        st.session_state.geo_request = True
        # Limpio valores previos para evitar confusión
        asesor["lat"] = None
        asesor["lon"] = None
        asesor["maps_url"] = None

    # Si se solicitó, hago la llamada *fuera* del botón (para que funcione en el rerun)
    if st.session_state.geo_request:
        loc = get_geolocation()
        if loc and "coords" in loc and loc["coords"].get("latitude") is not None:
            lat = float(loc["coords"]["latitude"])
            lon = float(loc["coords"]["longitude"])
            asesor["lat"] = lat
            asesor["lon"] = lon
            asesor["maps_url"] = f"https://www.google.com/maps?q={lat},{lon}"
            st.session_state.geo_request = False  # listo, apago el flag
        else:
            st.info("Solicitando permiso o esperando la ubicación… Si ya aceptaste, espera un segundo o vuelve a intentar.")

with col2:
    if asesor["lat"] is not None and asesor["lon"] is not None:
        st.success(f"Ubicación: {asesor['lat']:.6f}, {asesor['lon']:.6f}")
        st.markdown(f"[Abrir en Google Maps]({asesor['maps_url']})")
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


