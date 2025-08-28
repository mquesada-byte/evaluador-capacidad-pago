# Home.py
import streamlit as st

st.set_page_config(page_title="Evaluador de Capacidad de Pago", page_icon="💻")

st.title("🏠 Evaluador de Capacidad de Pago")
st.write("Usa el menú lateral o el enlace de abajo para iniciar con el **Paso 1 – Datos del asesor**.")

st.divider()

# ÚNICO paso habilitado por ahora
with st.container(border=True):
    st.page_link(
        "pages/01_Asesor.py",
        label="➡️ 01 – Datos del asesor",
        help="Identificación del asesor, fecha/hora (CR) y geolocalización."
    )

st.divider()
st.info("También podés abrir el Paso 1 desde el menú lateral.")
