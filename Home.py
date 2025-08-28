import streamlit as st

st.set_page_config(page_title="Evaluador de Capacidad de Pago", page_icon="💻")

st.title("🏠 Evaluador de Capacidad de Pago")
st.write(
    "Bienvenido. Usa el menú lateral o el botón de abajo para iniciar con el **Paso 1 – Datos del asesor**."
)

col1, col2 = st.columns(2)

with col1:
    # Enlace visible (si por permisos del navegador no funciona switch_page)
    st.page_link("pages/01_Asesor.py", label="➡️ Abrir Paso 1 – Datos del asesor", help="Ir a la página del Asesor")

with col2:
    # Navegación programática (opcional)
    if st.button("Iniciar ahora ➡️ Paso 1", use_container_width=True, type="primary"):
        try:
            st.switch_page("pages/01_Asesor.py")
        except Exception:
            st.info("Si no navegó automáticamente, usa el enlace de la izquierda o el link de arriba.")

