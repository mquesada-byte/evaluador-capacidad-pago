# Home.py
import streamlit as st

st.set_page_config(page_title="Evaluador de Capacidad de Pago", page_icon="💻")

st.title("🏠 Evaluador de Capacidad de Pago")
st.write("Usa el menú lateral o los enlaces de abajo para navegar por los pasos.")

st.divider()

# Paso 1
with st.container(border=True):
    st.page_link(
        "pages/01_Asesor.py",
        label="➡️ 01 – Datos del asesor",
        help="Identificación del asesor, fecha/hora (CR) y geolocalización."
    )

# Paso 2
with st.container(border=True):
    st.page_link(
        "pages/02_Cliente_y_negocio.py",
        label="➡️ 02 – Cliente y negocio",
        help="Datos del cliente y del negocio para iniciar la evaluación."
    )

# Paso 3A
with st.container(border=True):
    st.page_link(
        "pages/03_Ventas_top_down.py",
        label=f"{step_status('done_03A')} 03A – Ventas (Top-down)",
        help="Declaración directa de ventas del último mes calendario."
    )

st.divider()
st.info("También podés abrir los pasos desde el menú lateral.")
