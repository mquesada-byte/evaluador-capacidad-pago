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

# Paso 6 – Valoración del asesor
with st.container(border=True):
    st.page_link(
        "pages/06_Valoración_asesor.py",  # usa el nombre exacto del archivo
        label=f"{step_status('done_06')} 06 – Valoración del asesor",
        help="Evaluación cualitativa (conocimiento, credibilidad, dudas y evidencia)."
    )

# Paso 7 – Conciliación de ventas
with st.container(border=True):
    st.page_link(
        "pages/07_Conciliación_de_ventas.py",  # usa el nombre exacto del archivo
        label=f"{step_status('done_07')} 07 – Conciliación de ventas",
        help="Compara Top-down, Bottom-up e Insumos y fija ventas conciliadas."
    )

# Paso 8 (Otros ingresos)
with st.container(border=True):
    st.page_link(
        "pages/08_Otros_ingresos.py",
        label=f"{step_status('done_08')} 08 – Otros ingresos del hogar",
        help="Registro y ponderación de otros ingresos del hogar."
    )

# Paso 9 – Deudas activas del hogar
with st.container(border=True):
    st.page_link(
        "pages/09_Deudas.py",
        label=f"{step_status('done_09')} 09 – Deudas activas del hogar",
        help="Préstamos/obligaciones vigentes; cuota mensual, saldos y clasificación por plazo."
    )

# Paso 10 – Gastos operativos
with st.container(border=True):
    st.page_link(
        "pages/10_Gastos_operativos.py",
        label=f"{step_status('done_10')} 10 – Gastos operativos",
        help="Gastos del negocio/hogar relacionados a la operación, mensualizados."
    )

# Paso 11 – Gastos familiares
with st.container(border=True):
    st.page_link(
        "pages/11_Gastos_familiares.py",
        label=f"{step_status('done_11')} 11 – Gastos familiares",
        help="Registro y mensualización de gastos del hogar, con opción de verificación/evidencia."
    )

# Paso 12 – Estado de Resultados
with st.container(border=True):
    st.page_link(
        "pages/12_Estado_de_resultadosl.py",  # nombre exacto del archivo
        label=f"{step_status('done_12')} 12 – Estado de resultados",
        help="Resumen automático de ventas, costos y gastos; calcula el disponible para préstamo."
    )

# Paso 13 – Balance general
with st.container(border=True):
    st.page_link(
        "pages/13_Balance_general.py",
        label=f"{step_status('done_13')} 13 – Balance general",
        help="Activos, pasivos, patrimonio y capital de trabajo."
    )

# --- Paso 14: Informe final (PDF) ------------------------
with st.sidebar:
    st.markdown("### Paso 14")
    if st.button("📑 Informe final (PDF)", key="go_step_14", use_container_width=True):
        try:
            st.switch_page("pages/14_Informe_final.py")
        except Exception:
            st.error("No se encontró: pages/14_Informe_final.py")

# (Si llevas conteo de progreso, recuerda subir el total a 14 y, opcionalmente,
# crear/usar la bandera st.session_state['done_14'] cuando se complete el paso 14.)

{"num": 14, "title": "Informe final (PDF)", "icon": "📑",
 "path": "pages/14_Informe_final.py", "done_key": "done_14"}

# Paso 15 – Análisis asistido (IA)
with st.container(border=True):
    st.page_link(
        "pages/15_Analisis_IA.py",
        label=f"{step_status('done_15')} 15 – Análisis asistido (IA)",
        help="Genera el análisis del caso con IA y permite descargarlo en PDF."
    )


st.divider()
st.info("También podés abrir los pasos desde el menú lateral.")


