# Home.py
import streamlit as st

st.set_page_config(page_title="Evaluador de Capacidad de Pago", page_icon="💻")

def step_status(flag: str) -> str:
    """Devuelve un emoji según si el paso ya fue completado en esta sesión."""
    return "✅" if st.session_state.get(flag) else "⏳"

st.title("🏠 Evaluador de Capacidad de Pago")
st.write("Usa el menú lateral o los enlaces de abajo para navegar por los pasos.")

st.divider()

# Paso 1
with st.container(border=True):
    st.page_link(
        "pages/01_Asesor.py",
        label=f"{step_status('done_01')} 01 – Datos del asesor",
        help="Identificación del asesor, fecha/hora (CR) y geolocalización."
    )

# Paso 2
with st.container(border=True):
    st.page_link(
        "pages/02_Cliente_y_negocio.py",
        label=f"{step_status('done_02')} 02 – Cliente y negocio",
        help="Datos del cliente y del negocio para iniciar la evaluación."
    )

# Paso 3A
with st.container(border=True):
    st.page_link(
        "pages/03_Ventas_top_down.py",
        label=f"{step_status('done_03A')} 03A – Ventas (Top-down)",
        help="Declaración directa de ventas del último mes calendario."
    )

# Paso 4 (Bottom-up)
with st.container(border=True):
    st.page_link(
        "pages/04_Ventas_botton_up.py",  # <- nombre exacto de tu archivo
        label=f"{step_status('done_04')} 04 – Ventas (Bottom-up)",
        help="Estimación operativa (clientes x ticket) para el último mes calendario."
    )

# Paso 5 (Insumos/Margen desde compras)
with st.container(border=True):
    st.page_link(
        "pages/05_Ventas_insumos_margen.py",
        label=f"{step_status('done_05')} 05 – Ventas (insumos/margen)",
        help="Estimación de ventas a partir de compras y margen declarado."
    )


st.divider()
st.info("También podés abrir los pasos desde el menú lateral.")


