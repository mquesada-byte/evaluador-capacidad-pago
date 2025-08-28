# Home.py
import streamlit as st

st.set_page_config(page_title="Evaluador de Capacidad de Pago", page_icon="💻")

st.title("🏠 Evaluador de Capacidad de Pago")
st.write("Usa el menú lateral o el enlace de abajo para iniciar con el recorrido")

st.divider()

# Datos del asesor
with st.container(border=True):
    st.page_link(
        "pages/01_Asesor.py",
        label="➡️ 01 – Datos del asesor",
        help="Identificación del asesor, fecha/hora (CR) y geolocalización."
    )

# Datos del cliente y su negocio
with st.container(border=True):
    st.page_link(
        "pages/02_Cliente_y_negocio.py",   # <-- nombre con .py
        label="➡️ 02 – Cliente y negocio",
        help="Datos del cliente/negocio para iniciar la evaluación."
    )


st.divider()
st.info("También puedes abrir los diferentes pasos desde el menú lateral.")
