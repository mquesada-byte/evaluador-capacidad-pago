# Home.py
import streamlit as st

st.set_page_config(page_title="Evaluador de Capacidad de Pago", page_icon="💻")

def step_status(flag: str) -> str:
    """Devuelve un emoji según si el paso ya fue completado en esta sesión."""
    return "✅" if st.session_state.get(flag) else "⏳"

def has_openai_key() -> bool:
    """Detecta si está configurada la clave de OpenAI en Secrets."""
    try:
        return bool(st.secrets.get("OPENAI_API_KEY", "").strip())
    except Exception:
        return False

# ------------------ Encabezado ------------------
st.title("🏠 Evaluador de Capacidad de Pago")
st.write("Usa el menú lateral o los enlaces de abajo para navegar por los pasos.")

# Estado de la IA (para el paso 15)
if has_openai_key():
    st.success("🔑 IA habilitada: se detectó **OPENAI_API_KEY** en *Settings → Secrets*.")
else:
    st.warning("⚠️ IA deshabilitada: agrega **OPENAI_API_KEY** en *Settings → Secrets* para usar el Paso 15.")

st.divider()

# ------------------ Navegación por pasos ------------------

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

# Paso 4 (Bottom-up)  ← conserva el nombre exacto de tu archivo
with st.container(border=True):
    st.page_link(
        "pages/04_Ventas_botton_up.py",
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
        "pages/06_Valoración_asesor.py",
        label=f"{step_status('done_06')} 06 – Valoración del asesor",
        help="Evaluación cualitativa (conocimiento, credibilidad, dudas y evidencia)."
    )

# Paso 7 – Conciliación de ventas
with st.container(border=True):
    st.page_link(
        "pages/07_Conciliación_de_ventas.py",
        label=f"{step_status('done_07')} 07 – Conciliación de ventas",
        help="Compara Top-down, Bottom-up e Insumos y fija ventas conciliadas."
    )

# Paso 8 – Otros ingresos
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
        "pages/12_Estado_de_resultadosl.py",
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

# Paso 14 – Informe final (PDF)
with st.container(border=True):
    st.page_link(
        "pages/14_Informe_final.py",
        label=f"{step_status('done_14')} 14 – Informe final (PDF)",
        help="Portada, resumen ejecutivo y descarga en PDF."
    )

# Paso 15 – Análisis asistido (IA)
# Se habilita solo si hay OPENAI_API_KEY y ya se completó el Paso 14
s15_disabled = not (has_openai_key() and st.session_state.get("done_14", False))
with st.container(border=True):
    # En algunos entornos es mejor evitar acentos en nombres de archivo.
    # Intentaremos abrir cualquiera de estas rutas cuando el botón se pulse.
    if st.button(
        f"{step_status('done_15')} 15 – Análisis asistido (IA)",
        use_container_width=True,
        disabled=s15_disabled,
        help="Genera el análisis del caso con IA y permite descargarlo en PDF."
    ):
        for candidate in [
            "pages/15_Analisis_IA.py",      # sin tilde (recomendado)
            "pages/15_Análisis_IA.py",      # con tilde (por si existe así)
        ]:
            try:
                st.switch_page(candidate)
                break
            except Exception:
                continue
        else:
            st.error("No se encontró el archivo de la página 15 (Analisis/Análisis IA). Verifica el nombre en la carpeta `pages/`.")

st.divider()
st.info("También podés abrir los pasos desde el menú lateral.")

