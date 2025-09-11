# pages/02_Cliente_y_negocio.py
import streamlit as st

# =========================
# PASO 2 – Datos del cliente y del negocio
# =========================
st.set_page_config(page_title="Paso 2: Cliente y negocio", page_icon="👤")

def init_paso2_state():
    st.session_state.setdefault("cliente", {})
    st.session_state.setdefault("negocio", {})
    c = st.session_state.cliente
    n = st.session_state.negocio

    # Cliente
    c.setdefault("nombre_completo", "")
    c.setdefault("identificacion", "")

    # Negocio
    n.setdefault("nombre_comercial", "")
    n.setdefault("persona_juridica", False)          # True/False
    n.setdefault("ubicacion", "")
    n.setdefault("sector_economico", "")             # comercio/servicios/industria
    n.setdefault("actividad_principal", "")
    n.setdefault("patente_municipal", False)
    n.setdefault("registros_contables", False)
    n.setdefault("tipo_local", "")
    n.setdefault("antiguedad_anios", 0)
    n.setdefault("antiguedad_meses", 0)

def antiguedad_str(anios:int, meses:int) -> str:
    return f"{anios} año(s) y {meses} mes(es)"

# --------- UI (sin usar 'step') ----------
init_paso2_state()
c = st.session_state.cliente
n = st.session_state.negocio

st.title("👤 Paso 2: Datos del cliente y del negocio")
st.caption("Complete los campos. Los marcados con * son obligatorios.")

with st.container():
    st.subheader("Datos del cliente")
    col1, col2 = st.columns(2)
    with col1:
        c["nombre_completo"] = st.text_input(
            "Nombre completo *",
            value=c["nombre_completo"],
            placeholder="Ej.: Juan Carlos Rodríguez"
        )
    with col2:
        c["identificacion"] = st.text_input(
            "Número de identificación (cédula, DIMEX, pasaporte) *",
            value=c["identificacion"],
            placeholder="Ej.: 1-2345-0678"
        )

st.divider()

st.subheader("Datos del negocio")
colA, colB = st.columns(2)
with colA:
    n["nombre_comercial"] = st.text_input(
        "Nombre comercial del negocio *",
        value=n["nombre_comercial"],
        placeholder="Ej.: Mini Súper La Esquina"
    )
    n["persona_juridica"] = st.selectbox(
        "¿Es persona jurídica?",
        options=["No", "Sí"],
        index=1 if n["persona_juridica"] else 0
    ) == "Sí"
    n["sector_economico"] = st.selectbox(
        "Sector económico *",
        options=["", "Comercio", "Servicios", "Industria"],
        index=["", "Comercio", "Servicios", "Industria"].index(n["sector_economico"]) if n["sector_economico"] in ["", "Comercio", "Servicios", "Industria"] else 0
    )
    n["actividad_principal"] = st.text_input(
        "Actividad económica principal *",
        value=n["actividad_principal"],
        placeholder="Ej.: Tienda de abarrotes / Salón de belleza / Agricultura"
    )
with colB:
    n["ubicacion"] = st.text_area(
        "Ubicación del negocio (dirección física)",
        value=n["ubicacion"],
        placeholder="Provincia, cantón, distrito, señas…",
        height=96
    )
    n["patente_municipal"] = st.selectbox(
        "¿Cuenta con patente municipal?",
        options=["No", "Sí"],
        index=1 if n["patente_municipal"] else 0
    ) == "Sí"
    n["registros_contables"] = st.selectbox(
        "¿Lleva registros contables?",
        options=["No", "Sí"],
        index=1 if n["registros_contables"] else 0
    ) == "Sí"

colC, colD = st.columns([0.5, 0.5])
with colC:
    n["tipo_local"] = st.selectbox(
        "Tipo de local *",
        options=["", "Propio", "Alquilado", "Ambulante", "Casa de habitación", "Otro"],
        index=["", "Propio", "Alquilado", "Ambulante", "Casa de habitación", "Otro"].index(n["tipo_local"]) if n["tipo_local"] in ["", "Propio", "Alquilado", "Ambulante", "Casa de habitación", "Otro"] else 0
    )
with colD:
    st.markdown("**Antigüedad del negocio (años/meses en operación)***")
    colY, colZ = st.columns(2)
    with colY:
        n["antiguedad_anios"] = st.number_input(
            "Años", min_value=0, max_value=80, step=1, value=int(n["antiguedad_anios"])
        )
    with colZ:
        n["antiguedad_meses"] = st.number_input(
            "Meses", min_value=0, max_value=11, step=1, value=int(n["antiguedad_meses"])
        )
    st.caption(f"Antigüedad: {antiguedad_str(n['antiguedad_anios'], n['antiguedad_meses'])}")

st.divider()

# -------- Validación obligatorios --------
obligatorios_ok = all([
    c["nombre_completo"].strip(),
    c["identificacion"].strip(),
    n["nombre_comercial"].strip(),
    n["sector_economico"] in ["Comercio", "Servicios", "Industria"],
    n["actividad_principal"].strip(),
    n["tipo_local"] in ["Propio", "Alquilado", "Ambulante", "Casa de habitación", "Otro"],
    (n["antiguedad_anios"] > 0 or n["antiguedad_meses"] > 0)
])

colNav1, colNav2 = st.columns([0.5, 0.5])
with colNav1:
    if st.button("⬅️ Volver al Paso 1", key="back_to_step_1", use_container_width=True):
        st.switch_page("pages/01_Asesor.py")

with colNav2:
    # Guardar y avanzar
    if st.button("Siguiente ➡️", key="next_step_2", disabled=not obligatorios_ok, use_container_width=True):
        # preparar bloque de reporte
        st.session_state.setdefault("reporte", {})
        st.session_state["reporte"]["cliente_negocio"] = {
            "cliente_nombre": c["nombre_completo"].strip(),
            "cliente_identificacion": c["identificacion"].strip(),
            "nombre_comercial": n["nombre_comercial"].strip(),
            "persona_juridica": "Sí" if n["persona_juridica"] else "No",
            "ubicacion": n["ubicacion"].strip(),
            "sector_economico": n["sector_economico"],
            "actividad_principal": n["actividad_principal"].strip(),
            "patente_municipal": "Sí" if n["patente_municipal"] else "No",
            "registros_contables": "Sí" if n["registros_contables"] else "No",
            "tipo_local": n["tipo_local"],
            "antiguedad": antiguedad_str(n["antiguedad_anios"], n["antiguedad_meses"]),
        }
        st.session_state["done_02"] = True

        # Ir directo al Paso 3A – Ventas Top-down
        try:
            st.switch_page("pages/03_Ventas_top_down.py")
        except Exception:
            st.success("Datos guardados. Abre el **Paso 3A – Ventas Top-down** desde el menú lateral.")
            st.stop()


